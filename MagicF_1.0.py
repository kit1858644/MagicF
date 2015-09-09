from PyQt5 import QtWidgets as Qtw, QtGui, QtCore
import sys, os, sqlite3, datetime, suos, subprocess

class Main():
	"""執行類"""
	def __init__(self):
		"""初始化所有程式必用數據"""

			# 初始提示信息
		if not os.path.exists("Keys.pyd"): MainWin.messBox(MainWin, titile = "- Welcome -", mess = "Please read the ReadMe before using.")

		self.s3c = sqlite3.connect("Keys.pyd")
		self.curs = self.s3c.cursor()

		self.oldbd = False 			# 方便日後更新數據庫
		self.version = "1.0"

			# 如果數據庫不存在, 創造版本表和主數據表
		self.curs.execute("create table if not exists version(version text)")
		self.curs.execute("create table if not exists hidden(path text, date text)")

		old_version = self.curs.execute("select version from version").fetchone()
			# 如果沒有舊版本號寫入版本數據庫
		if not old_version: self.curs.execute("insert into version values('{0}')".format(self.version))
			# 如果有舊版本號, 對比/更新
		elif old_version[0] != self.version:
			self.curs.execute("update version set version = '{0}'".format(self.version))
			self.oldbd = True

	def hiDden(self, paths, opened, class_mainwin):
		"""隱藏文件, class_mainwin 為MainWin的self"""
			# 日期
		today = datetime.date.today().strftime("%d-%m-%Y")
			# 如果文件已在數據庫, 提醒
		exis_file = []

			# 把文件寫入數據庫
		for path in paths:
				# 取得所有已隱藏列表
			if self.curs.execute("select * from hidden where path=:path", {"path": path}).fetchone(): exis_file.append(path)
				# 自動判斷文件夾/文件, 寫入數據庫
			elif os.path.isdir(path):
				subprocess.call(r'attrib /S /D +h +s "{0}/*"'.format(path), shell=True)
				subprocess.call(r'attrib +h +s "{0}"'.format(path), shell=True)
				self.curs.execute("insert into hidden values('{0}', '{1}')".format(path, today))
			elif os.path.isfile(path):
				subprocess.call(r'attrib +h +s "{0}"'.format(path), shell=True)
				self.curs.execute("insert into hidden values('{0}', '{1}')".format(path, today))
			# 統一寫入
		self.s3c.commit()		

			# 如果UI為擴展狀態, 更新列表
		if opened: class_mainwin.openDb()
			# 已存在列表提醒
		if exis_file: MainWin.messBox(MainWin, titile = "- Hidden -", mess = "{0} files are already hidden.".format(len(exis_file))
										, messicon = Qtw.QMessageBox.Information , detail = exis_file)

	def unhiDe(self, paths, class_mainwin):
		"""取消隱藏文件"""
		if not paths: MainWin.messBox(MainWin, titile = "- Error -", mess = "Select one path or more.")

		for path in paths:
				# 自動判斷文件夾/文件, 寫入數據庫
			if os.path.isdir(path):
				subprocess.call(r'attrib /S /D -h -s "{0}/*"'.format(path), shell=True)
				subprocess.call(r'attrib -h -s "{0}"'.format(path), shell=True)
				self.curs.execute("delete from hidden where path=:path", {"path": path})
			elif os.path.isfile(path):
				subprocess.call(r'attrib -h -s "{0}"'.format(path), shell=True)
				self.curs.execute("delete from hidden where path=:path", {"path": path})
			# 更新數據庫, 清空已勾選項目 和 更新列表
		self.s3c.commit()
		MainWin.checklist.clear()
		class_mainwin.openDb()

	def exTract(self, paths, raw_path, class_mainwin):
		"""提取文件/文件夾"""
		if len(paths) < 1: MainWin.messBox(MainWin, titile = "- Error -", mess = "Select one path or more.", messicon = Qtw.QMessageBox.Warning); return

			# 檢查有沒有設定提取路徑
		try:
			ex_path = self.curs.execute("select * from ex_path").fetchone()[0]
		except sqlite3.OperationalError:
			MainWin.messBox(MainWin, titile = "- Error -", mess = "Please set the extract path first.", messicon = Qtw.QMessageBox.Warning)
			return

		miss_file = []	# 不存在文件
		extract_path = os.path.join(ex_path, "MagicF")	# 提取路徑

		if not os.path.exists(extract_path): os.mkdir(extract_path)

		for path in paths:
			exsitsed = False	# 是否已存在
			tar_path = os.path.join(extract_path, os.path.split(path)[1])	# 目標路徑

			if not os.path.exists(path): miss_file.append(path); continue
				# 文件已存在, 提示是否覆蓋
			if os.path.exists(tar_path): 
				if MainWin.messBox(MainWin, titile = "- Exists -", mess = "{0} already Exists\nDo you want to Overwrite?".format(tar_path)
						, messicon = Qtw.QMessageBox.Warning, setbutton = (Qtw.QMessageBox.Yes | Qtw.QMessageBox.Cancel)) == Qtw.QMessageBox.Yes:
							exsitsed = True
				# 取消隱藏
			if os.path.isdir(path):
				subprocess.call(r'attrib /S /D -h -s "{0}/*"'.format(path), shell=True)
				subprocess.call(r'attrib -h -s "{0}"'.format(path), shell=True)
				
			elif os.path.isfile(path):
				subprocess.call(r'attrib -h -s "{0}"'.format(path), shell=True)

				# 移動文件
			suos.movep(path, extract_path, exsitsed)

			# 反排列已勾選行數
		class_mainwin.checkrow.sort(reverse = True)
			# 從深到淺刪除UI列表
		for x in class_mainwin.checkrow: class_mainwin.model.removeRow(x)

			# 清空列表
		class_mainwin.checklist.clear()
		class_mainwin.checkrow.clear()

		if miss_file: MainWin.messBox(MainWin, titile = "- Missing Files -", mess = "{0} files missing.\nParent directory may have been moved.".format(
						len(miss_file)), messicon = Qtw.QMessageBox.Critical, detail = miss_file)
			# 更新UI列表
		class_mainwin.extract_Ui(raw_path, just_refresh = True)

class Button(Qtw.QPushButton):
	"""重載QPushButton"""
	def __init__(self, parent, main):
		super().__init__()
		self.parent = parent
		self.main = main
		self.setAcceptDrops(True)
			# 右鍵菜單
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)  
		self.customContextMenuRequested.connect(self.aboutMenu)
			# 加入右鍵菜單
		self.infomenu = Qtw.QMenu(self)    
			# 菜單內容
		self.action = self.infomenu.addAction(QtGui.QIcon("magic.ico"), "T1me")
		self.action.triggered.connect(lambda: MainWin.messBox(self.parent, titile = " ", mess = 'Version: <a style= "color:#55aaff; text-decoration:none; \
									font-size:14pt; font-family:Consolas; font-weight: bold;" href=\"http://pan.baidu.com/s/1gd8QXvP\">{0}</a>'.format(self.main.version)))

	def aboutMenu(self, pos): 
		"""顯示右鍵菜單"""
		self.infomenu.exec_(QtGui.QCursor.pos())
		self.infomenu.show() 

	def dragEnterEvent(self, event):
		"""拖進事件"""
			# 接受拖放
		event.accept()

	def dropEvent(self, event):
		"""拖放事件"""
			# 取得文件名
		urlform = event.mimeData().urls()
		files = [url.toLocalFile() for url in urlform]
			# 隱藏文件
		Main.hiDden(self.main, files, self.parent.opened, self.parent)

class MainWin(Qtw.QWidget):
	"""主UI 類"""

	checklist = []	# 勾選項目
	checkrow = []	# 勾選行數

	def __init__(self):
		super().__init__()
		self.main = Main()
		self.opened = False		# UI是否已擴展
		self.extract_mode = False	# UI是否提取模式

		self.win()
		
	def win(self):
		"""主GUI"""
		self.setWindowTitle("MagicF")
		self.setWindowIcon(QtGui.QIcon("magic.ico"))
		self.setFixedSize(233, 104)
			# 窗口置頂
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
			# layout
		self.vbox = Qtw.QVBoxLayout(self)
		self.vbox.setSpacing(0)
		self.vbox.setContentsMargins(0,0,0,0)
			# 重載的Button
		b1 = Button(self, self.main)
		b1.setIcon(QtGui.QIcon("add.png"))
		b1.setIconSize(QtCore.QSize(104,104))
		b1.clicked.connect(self.openDb)
			# 加入和設置layout
		self.vbox.addWidget(b1)
		self.setLayout(self.vbox)

	def checkBox(self, index):
		"""取得自定Service名"""
			# 如果行被勾選: 寫入self.checklist, 如果被取除勾選, 從self.checklist刪除
		if index.checkState(): 
			self.checklist.append(index.text())
			self.checkrow.append(index.row())
		else:
			if index.text() in self.checklist: 
				self.checklist.remove(index.text())
				self.checkrow.remove(index.row())

	def openDb(self): 
		"""開啟數據庫"""
		def loadDb():
			"""更新列表"""
			miss_path = []

			data = self.main.curs.execute("select * from hidden").fetchall()		# 取得所有已隱藏列表

				# 如果數據庫不為空, 更新
			if data:
			
				self.model.clear()
				self.model.setHorizontalHeaderLabels(["Path", "Date"])

				for path, date in data:
						# 如果列表中的路徑已不存在, 更新數據庫
					if not os.path.exists(path): 
						miss_path.append(path)															# 
						self.main.curs.execute("delete from hidden where path=:path", {"path": path})

						# 寫入UI列表
					else:
						path_item = QtGui.QStandardItem(path)
						path_item.setCheckable(True)
						path_item.setEditable(False)
						date_item = QtGui.QStandardItem(date)
						date_item.setEditable(False)
						self.model.appendRow([path_item,date_item])	

				self.main.s3c.commit()

					# 當有文件被移動或刪除警告, 寫入log
				if miss_path:
					with open("Missing_files.log", "w", encoding = "utf-8") as missing: 
						missing.write('''\t\t--- Missing Files ---\n\n# Program can't find These file.\n# These files may have been moved or deleted.\n\n''')
						[missing.write("- {0}\n\n".format(x)) for x in miss_path]
					self.messBox(titile = "- Missing Files -", mess = "{0} files missing.\nPlease Check the Missing_files.log !".format(
								len(miss_path)), messicon = Qtw.QMessageBox.Critical)

				return True

				# 如果UI已擴展時, 但data沒有數據, 關閉擴展
			elif self.opened:
				self.treev.deleteLater()
				self.initb.deleteLater()
				self.delb.deleteLater()
				self.extract.deleteLater()
				self.setFixedSize(233, 104)

				self.opened = False

			# 如果不存在數據庫, 提示
		if not os.path.exists("Keys.pyd"):
			self.messBox(titile = "- NO Data -", mess = "Can't find any data.", messicon = Qtw.QMessageBox.Information)

			# 如果UI 沒有擴展, 擴展UI和設定列表
		elif not self.opened:
				# 列表樹
			self.treev = Qtw.QTreeView()
			self.model = QtGui.QStandardItemModel(self.treev)

			if loadDb():

				self.hbox = Qtw.QHBoxLayout(self)
					# 設定模式和取消樹列形式
				self.treev.setModel(self.model)
				self.treev.setRootIsDecorated(False)

				self.initb = Qtw.QPushButton("&init", self)
				self.initb.setFont(QtGui.QFont("Consolas",13, True))
				self.initb.setFixedWidth(40)
				self.initb.clicked.connect(self.init_Method)

				self.delb = Qtw.QPushButton("&Unhide", self)
				self.delb.setFont(QtGui.QFont("Consolas",13, True))
				self.delb.clicked.connect(lambda: Main.unhiDe(self.main, self.checklist, self))

				self.extract = Qtw.QPushButton("&Ex", self)
				self.extract.setFont(QtGui.QFont("Consolas",13, True))
				self.extract.setFixedWidth(40)	
				self.extract.clicked.connect(lambda: self.extract_Ui(self.checklist, raw = True))

					# 當row Checkbox被點擊事件
				self.model.itemChanged.connect(self.checkBox)
				self.setFixedSize(250, 302)

				self.treev.setColumnWidth(0, 175)

				self.vbox.addWidget(self.treev)

				self.hbox.addWidget(self.initb)
				self.hbox.addWidget(self.delb)				
				self.hbox.addWidget(self.extract)

				self.vbox.addLayout(self.hbox)

				self.opened = True
			else:
				self.messBox(titile = "- NO Data -", mess = "Can't find any data.", messicon = Qtw.QMessageBox.Information)

			# 退出提取模式
		elif self.extract_mode:
			self.extract_mode = False

			self.checklist.clear()
			self.checkrow.clear()

			self.set_path.deleteLater()
			self.extract_2.deleteLater()
			self.goback.deleteLater()

			self.initb.show()
			self.delb.show()
			self.extract.show()

			loadDb()
			self.treev.setColumnWidth(0, 175)
			# 簡單的更新列表
		else:
			loadDb()
			self.treev.setColumnWidth(0, 175)

	def init_Method(self):
		"""初始化程式"""
		if os.path.exists("Keys.pyd"):
			if self.messBox(titile = "- Warning -", mess = "Initialization will delete all hidden history data.\n\nNote: All hidden files won't Unhide automatic"\
							, setbutton = (Qtw.QMessageBox.Yes | Qtw.QMessageBox.Cancel)) == Qtw.QMessageBox.Yes:
				self.main.curs.close()
				self.main.s3c.close()
				os.remove("Keys.pyd")
				self.messBox(titile = "- Initialization -", mess = "Successful initialization!\n\nPlease Restart MagicF.")
				self.exit()
		else:
			self.messBox(titile = "- NO Data -", mess = "Can't find any data.", messicon = Qtw.QMessageBox.Information)

	def extract_Ui(self, path, raw = False, just_refresh = False):
		"""提取模式UI, raw: 記錄path"""
		def reFresh():
			"""更新提取模式列表"""
			self.model.clear()
			self.model.setHorizontalHeaderLabels(["Hidden Path"])

			for files in os.walk(path[0]):
				path_item = QtGui.QStandardItem(files[0])
				path_item.setCheckable(True)
				path_item.setEditable(False)
				self.model.appendRow([path_item])	

				for x in files[-1]:
					path_item = QtGui.QStandardItem(files[0] + "/" + x)
					path_item.setCheckable(True)
					path_item.setEditable(False)
					self.model.appendRow([path_item])

		if len(path) > 1: self.messBox(titile = "- Error -", mess = "Selected more than one path.", messicon = Qtw.QMessageBox.Warning)
		elif len(path) < 1: self.messBox(titile = "- Error -", mess = "Select a path.", messicon = Qtw.QMessageBox.Warning)
		elif not os.path.isdir(path[0]): self.messBox(titile = "- Error -", mess = "Path must be a directory.", messicon = Qtw.QMessageBox.Warning)
		else:
			reFresh()
				# 只更新列表
			if just_refresh: return
				# 用不能改變的元祖儲存, 以防改變
			if raw: self.raw_path = (path[0],)
			self.extract_mode = True
				# 關閉隱藏模式的按鍵
			self.initb.close()
			self.delb.close()
			self.extract.close()
				# 設定提取模式的按鍵
			self.set_path = Qtw.QPushButton("&Path", self)
			self.set_path.setFont(QtGui.QFont("Consolas",13, True))
			self.set_path.setFixedWidth(50)
			self.set_path.clicked.connect(self.setPath)

			self.extract_2 = Qtw.QPushButton("&Extract", self)
			self.extract_2.setFont(QtGui.QFont("Consolas",13, True))
			self.extract_2.clicked.connect(lambda: Main.exTract(self.main, self.checklist, self.raw_path, self))

			self.goback = Qtw.QPushButton("<--", self)
			self.goback.setFont(QtGui.QFont("Consolas",13, True))
			self.goback.setFixedWidth(50)
			self.goback.clicked.connect(self.openDb)

			self.hbox.addWidget(self.set_path)
			self.hbox.addWidget(self.extract_2)
			self.hbox.addWidget(self.goback)
				# 清除隱藏模式列表
			self.checklist.clear()
			self.checkrow.clear()

	def setPath(self):
		"""設定提取路徑"""
			# 打開文件夾
		path = Qtw.QFileDialog.getExistingDirectory(self, "Select Extract Folder")
			# 如果數據庫不存在, 創造版本表和主數據表
		self.main.curs.execute("create table if not exists ex_path(ex_path text)")

		old_path = self.main.curs.execute("select ex_path from ex_path").fetchone()
			# 如果沒有路徑寫入路徑數據庫
		if not old_path: self.main.curs.execute("insert into ex_path values('{0}')".format(path))
			# 如果有路徑, 對比/更新
		elif old_path[0] != path: self.main.curs.execute("update ex_path set ex_path = '{0}'".format(path))

		self.main.s3c.commit()

	def closeEvent(self, event):
		self.main.curs.close()
		self.main.s3c.close()

	def messBox(self, titile, mess, setbutton = None, messicon = None, detail = []):
		"""通用信息框"""
		messbox = Qtw.QMessageBox()
		messbox.setWindowTitle(titile)
		messbox.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		messbox.setWindowIcon(QtGui.QIcon("magic.ico"))
		messbox.setText(mess)
		messbox.setFont(QtGui.QFont("Consolas", 13, True))

			# 先定Icon
		if messicon: messbox.setIcon(messicon)
			# 自定Button
		if setbutton: messbox.setStandardButtons(setbutton)
			# 如有詳細信息, 啟用
		if detail: 
			text = ""
			for x in detail: text += "- {0}\n".format(x)
			messbox.setDetailedText(text)
			# 反回MessBox的按鍵碼
		return messbox.exec_()

if __name__ == "__main__":
	app = Qtw.QApplication([])
	win = MainWin()
	win.show()
	sys.exit(app.exec_())

# =============================
# Plan
# 新增一個初始
# -----------------------------
# Creat by T1me
# Date: 21-8-2015
#
# Change Log
#
# Beta
# 22-8-2015:	完成初版
# Beta_1
# 23-8-2015:	增加對文件被移動或刪除檢測
#				修正數據庫不正常關閉
#				增加版本號數據表
#				加入版本信息
# Beta_2
# 24-8-2015:	可提取隱藏文件夾內的內容
# Beta_3
# 27-8-2015:	修正提取不了文件夾問題
#				修正extract_ui path 自動改變問題
#				修正extract沒選項問題
#				修父目錄已被移動下, 選擇目錄的文件
#				加入快捷鍵
# Beta_4
# 7-9-2015:		修正在移動已存在文件夾時出錯
# 				修正在提取文件夾時, 會再自動隱藏所有文件
# Beta_5
# 8-9-2015:		增加自定提取文件夾
#				增加版本URL
# 1.0
# 9-9-2015:		優化
#				全詮釋
#				新增初始化