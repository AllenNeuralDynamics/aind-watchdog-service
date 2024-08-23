"""Hook file for PyInstaller: AIND Data Schema Models package."""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("aind_data_schema_models", include_py_files=True)
