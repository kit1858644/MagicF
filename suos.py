import os, shutil

def movep(src, dst, overlay = True):
	""" 移動文件
		overlay: True / False, True為自動覆蓋 """

	if not os.path.isdir(dst): raise TypeError("dst must be a directory.")

		# 移動文件
	if os.path.isfile(src):
		dst_dir = os.path.join(dst, os.path.basename(src))

		if os.path.exists(dst_dir): 
			if not overlay: return
			os.remove(dst_dir)
		os.rename(src, dst_dir)
		return

		# 移動文件夾
	for folder in os.walk(src):
			# 把目標路徑, 系統分隔符 和 src 文件夾的子路徑合成一層路徑
		dst_dir = dst + os.sep + os.path.basename(src) + folder[0].split(src, 1)[-1]
			# 當路徑已存在於目標文件夾, 刪除目標文件夾的文件, 再把新的文件移動
		if os.path.exists(dst_dir):
			for exs_file in folder[-1]:
				abs_path = os.path.join(dst_dir, exs_file)
				if os.path.exists(abs_path): 
					if not overlay: continue
					os.remove(abs_path)
				os.rename(os.path.join(folder[0], exs_file), os.path.join(dst_dir, exs_file))

		elif not os.path.exists(dst_dir): shutil.move(folder[0], dst_dir)

		# 刪除移動後的空文件夾
	if os.path.exists(src) and overlay: shutil.rmtree(src)