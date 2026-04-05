import argparse
import base64
import json
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def sign_payload(private_key: Ed25519PrivateKey, payload: dict) -> str:
    payload_raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = private_key.sign(payload_raw)
    return f"{b64url_encode(payload_raw)}.{b64url_encode(signature)}"


def load_private_key(path: str) -> Ed25519PrivateKey:
    with open(path, "rb") as fh:
        return serialization.load_pem_private_key(fh.read(), password=None)


def issue_serial(args):
    slot = int(args.slot)
    if slot < 1 or slot > 3:
        raise SystemExit("slot must be between 1 and 3")

    priv = load_private_key(args.private_key)
    payload = {
        "product": args.product,
        "license_id": args.license_id,
        "device_id": args.device_id.strip().upper(),
        "slot": slot,
    }

    serial = sign_payload(priv, payload)
    print(serial)


def issue_three(args):
    priv = load_private_key(args.private_key)
    device_ids = [x.strip().upper() for x in args.device_ids.split(",") if x.strip()]
    if len(device_ids) != 3:
        raise SystemExit("device_ids must contain exactly 3 comma-separated ids")

    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)

    for idx, dev in enumerate(device_ids, start=1):
        payload = {
            "product": args.product,
            "license_id": args.license_id,
            "device_id": dev,
            "slot": idx,
        }
        serial = sign_payload(priv, payload)
        file_name = f"serial_slot{idx}_{dev}.txt"
        out_path = os.path.join(out_dir, file_name)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(serial + "\n")
        print(f"Serial TXT created: {out_path}")


def _self_destruct_tools_folder():
    import shutil, time

    tools_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Self-destruct: Deleting tools folder in 3 seconds: {tools_dir}")
    time.sleep(3)  # Give time for user to see output

    try:
        shutil.rmtree(tools_dir)
        print("Tools folder deleted successfully.")
    except Exception as e:
        print(f"Warning: Could not delete tools folder: {e}")
        # Fallback: create a batch to delete later
        batch_path = os.path.join(tools_dir, "cleanup_tools.bat")
        with open(batch_path, "w", encoding="utf-8") as fh:
            fh.write("@echo off\n")
            fh.write("timeout /t 5 /nobreak >nul\n")
            fh.write(f"rd /s /q \"{tools_dir}\"\n")
            fh.write("exit /b 0\n")
        print(f"Fallback cleanup batch created: {batch_path}")
        os.startfile(batch_path)


def issue_serial_to_txt(args):
    from app.licensing import get_device_id

    if args.device_id:
        device_id = args.device_id.strip().upper()
    else:
        device_id = get_device_id()

    if not device_id:
        raise SystemExit("Unable to determine device ID")

    slot = int(args.slot)
    if slot < 1 or slot > 3:
        raise SystemExit("slot must be between 1 and 3")

    priv = load_private_key(args.private_key)
    payload = {
        "product": args.product,
        "license_id": args.license_id,
        "device_id": device_id,
        "slot": slot,
    }
    serial = sign_payload(priv, payload)

    out = args.output or os.path.join(".", f"serial_{device_id}.txt")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(serial + "\n")

    print("Device ID:", device_id)
    print("Serial saved:", out)

    if args.self_destruct:
        print("Self-destruct: tools folder will be removed after script exits.")
        _self_destruct_tools_folder()


def main():
    parser = argparse.ArgumentParser(description="DyeMaster Pro serial generator")
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("issue-serial", help="Issue one serial for one device")
    p1.add_argument("--license-id", required=True)
    p1.add_argument("--device-id", required=True)
    p1.add_argument("--slot", required=True, type=int, choices=[1, 2, 3])
    p1.add_argument("--product", default="DyeMasterPro")
    p1.add_argument("--private-key", default="tools/license_private_key.pem")
    p1.set_defaults(func=issue_serial)

    p2 = sub.add_parser("issue-3", help="Issue 3 serials (one per device) as separate TXT files")
    p2.add_argument("--license-id", required=True)
    p2.add_argument("--device-ids", required=True, help="Comma separated 3 device ids")
    p2.add_argument("--product", default="DyeMasterPro")
    p2.add_argument("--private-key", default="tools/license_private_key.pem")
    p2.add_argument("--output-dir", default="tools/serials")
    p2.set_defaults(func=issue_three)

    p3 = sub.add_parser("issue-serial-local", help="Issue one serial for this device and write to txt")
    p3.add_argument("--license-id", required=True)
    p3.add_argument("--slot", required=True, type=int, choices=[1, 2, 3])
    p3.add_argument("--product", default="DyeMasterPro")
    p3.add_argument("--private-key", default="tools/license_private_key.pem")
    p3.add_argument("--device-id", default=None, help="Optional override device_id; if omitted uses local device fingerprint")
    p3.add_argument("--output", default=None, help="Output txt file path (default: serial_<deviceid>.txt)")
    p3.add_argument("--self-destruct", action="store_true", help="After generating serial, delete tools folder automatically")
    p3.set_defaults(func=issue_serial_to_txt)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
