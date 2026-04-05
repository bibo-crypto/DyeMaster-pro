DyeMaster Pro - Quick Run & Activation Guide

1) Build EXE
- Open PowerShell in project folder.
- Run:
  pyinstaller DyeMasterPro.spec --clean
- Confirm file exists:
  dist\DyeMasterPro\DyeMasterPro.exe

2) Build Installer (Inno Setup)
- Open installer.iss in Inno Setup Compiler.
- Click Compile.
- Output installer is usually:
  installer_output\DyeMasterPro_Setup.exe

3) Get Device ID (on customer machine)
- Run in project folder (or same code environment):
  python -c "from app.licensing import get_device_id; print(get_device_id())"
- Example output:
  A96273E3187A12D3923E

4) Generate Serial for this device (seller side)
- IMPORTANT: do NOT use < > in PowerShell.
- Run:
  python tools\license_admin.py issue-serial --license-id LIC-LOCAL-001 --device-id A96273E3187A12D3923E --slot 1
- Copy the output text (long one-line code). This is the serial.

5) Install and Activate
- Run DyeMasterPro_Setup.exe.
- Installer asks for Serial Code.
- Paste the serial exactly as generated.
- Finish installation and launch app.

6) 3 Devices only
- For second and third devices, repeat steps 3 and 4 with:
  --slot 2
  --slot 3
- Each device MUST use its own Device ID and its matching serial.

7) Generate 3 serial files at once
- Run:
  python tools\license_admin.py issue-3 --license-id LIC-001 --device-ids DEV1,DEV2,DEV3 --output-dir tools/serials
- Creates:
  tools/serials/serial_slot1_DEV1.txt
  tools/serials/serial_slot2_DEV2.txt
  tools/serials/serial_slot3_DEV3.txt

Troubleshooting
- Error about '<' operator in PowerShell:
  You typed <DEVICE_ID> literally. Replace with real ID without < >.
- App says serial does not belong to this device:
  Generate serial again using the exact Device ID from that machine.
- Keep this file private:
  tools/license_private_key.pem
  Never ship private key with customer installer.
