import glob
import os

# 합칠 폴더 상대경로 (현재 스크립트 기준)
files_to_merge = glob.glob("/home/stongone123/freqtrade/src/utils/*.py")
files_to_merge.sort(key=os.path.getmtime)  # 최근수정순

output_file = "/home/stongone123/freqtrade/chat_gpt/utils.py"

with open(output_file, "w", encoding="utf-8") as outfile:
    for fname in files_to_merge:
        with open(fname, "r", encoding="utf-8") as infile:
            outfile.write(f"# ===== {fname} 시작 =====\n")
            outfile.write(infile.read())
            outfile.write(f"\n# ===== {fname} 끝 =====\n\n")

print(f"✅ 병합 파일 [{output_file}]로 생성 완료!")