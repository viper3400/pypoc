# Run from the repository root:
# uv run pyinstaller --clean --noconfirm packaging/platform-server.spec

from importlib.metadata import PackageNotFoundError, entry_points
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata


block_cipher = None
project_root = Path(SPECPATH).parent
entry_point_group = "flask_plugin_platform.plugins"
plugin_modules = []
plugin_packages = set()
metadata = []
datas = collect_data_files("flask_plugin_platform")

try:
    metadata += copy_metadata("flask-plugin-platform")
except PackageNotFoundError:
    pass

for entry_point in entry_points().select(group=entry_point_group):
    module_name = entry_point.value.split(":", maxsplit=1)[0]
    package_name = module_name.split(".", maxsplit=1)[0]
    plugin_modules.append(module_name)
    plugin_packages.add(package_name)
    if entry_point.dist is not None:
        distribution_name = entry_point.dist.metadata["Name"]
        try:
            metadata += copy_metadata(distribution_name)
        except PackageNotFoundError:
            pass

for package_name in sorted(plugin_packages):
    datas += collect_data_files(package_name)


a = Analysis(
    [str(project_root / "flask_plugin_platform" / "cli.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas + metadata,
    hiddenimports=plugin_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="platform-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
