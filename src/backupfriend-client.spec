# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['backupfriend-client.py'],
             binaries=[('rdiff-backup.exe', 'bin'), ('ssh_bin/cygcrypto-1.1.dll', 'bin'), ('ssh_bin/cygwin1.dll', 'bin'), ('ssh_bin/cyggssapi_krb5-2.dll', 'bin'), ('ssh_bin/cygz.dll', 'bin'), ('ssh_bin/ssh.exe', 'bin')],
             datas=[('backupfriend\\config', 'backupfriend\\config'), ('backupfriend\\images', 'backupfriend\\images'), ('backupfriend\\res', 'backupfriend\\res')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='backupfriend-client',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='backupfriend-client')
