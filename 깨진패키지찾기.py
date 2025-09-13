import pathlib

site_packages = pathlib.Path(r"C:\Users\STD11\AppData\Local\Programs\Python\Python313\Lib\site-packages")

broken_files = []
for metadata_file in site_packages.rglob("METADATA"):
    try:
        metadata_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        broken_files.append((metadata_file, str(e)))
    except PermissionError:
        print(f"⚠️ 접근 불가: {metadata_file} (건너뜀)")

if broken_files:
    print("🚨 깨진 METADATA 파일 발견!")
    for path, error in broken_files:
        print(f"- {path} (에러: {error})")
else:
    print("✅ 깨진 METADATA 파일 없음 (다른 문제일 수도 있음)")
