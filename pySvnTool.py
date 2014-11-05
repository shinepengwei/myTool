# -*- coding: utf-8 -*- 
#tools.py  公共工具集，主要是使用python对文件夹进行svn操作

import pysvn
import filecmp
import sys
import os
import shutil

def get_login( realm, username, may_save ):
	
	return True, "", "",False


svn_client_inst = pysvn.Client();
svn_client_inst.exception_style = 1
svn_client_inst.callback_get_login = get_login


def ignore_svn(path, names):
	return ['.svn']

#递归拷贝src到dst文件夹，如果目标已存在，则不进行拷贝
#拷贝过程会忽略.svn文件
def copy_dir(src, dst):
	print("copy:" + src + "\tto:" + dst)  
	files = os.listdir(src)  
	for file in files:
		if file == '.svn':
			continue
		fileSrc = os.path.join(src,file)
		fileDst = os.path.join(dst,file)
		if os.path.exists(fileDst):  
			if os.path.isfile(fileSrc):  
				print(fileSrc + " is already exist.")  
			else:  
		# 递归  
				copy_dir(fileSrc, fileDst)  
		else:  
			if os.path.isfile(fileSrc):  
				shutil.copy2(fileSrc,fileDst)  
			else:
				shutil.copytree(fileSrc,fileDst,ignore=ignore_svn)  

#筛选src中的文件和文件夹，如果在exclude_list中，则拷贝到exclude_copy_dst
def copy_dir_filter(src, dst, exclude_copy_dst="", exclude_list=[]):
	files = os.listdir(src)
	for file in files:
		if file == '.svn':
			continue
		print "handling file: "+file+"from" + src + " to " + dst +" "+ exclude_copy_dst

		fileSrc = os.path.join(src,file)
		fileDst = os.path.join(dst,file)
		exclude_dst = os.path.join(exclude_copy_dst, file)

		if os.path.isfile(fileSrc):
			if file in exclude_list:
				if not os.path.exists(exclude_copy_dst):
					os.makedirs(exclude_copy_dst)
				shutil.copy2(fileSrc, exclude_dst)
			else:
				if not os.path.exists(dst):
					os.makedirs(dst)
				shutil.copy2(fileSrc,fileDst)
		else:
			if file in exclude_list:
				if not os.path.exists(exclude_dst):
					os.makedirs(exclude_dst)
				copy_dir_filter(fileSrc,exclude_dst)
			else:
				if not os.path.exists(fileDst):
					os.makedirs(fileDst)
				copy_dir_filter(fileSrc,fileDst, exclude_dst, exclude_list)

def svn_up(path, revision=None, revert=True):
	print 'svn_up', path
	success = True
	revision=pysvn.Revision( pysvn.opt_revision_kind.number, revision ) if revision else pysvn.Revision( pysvn.opt_revision_kind.head )


	#出error或者其他失败原因，都马上中止函数并返回false
	try:
		if revert:
			if svn_client_inst.revert(path, True) == -1:
				success = False
		if svn_client_inst.update(path, True, revision) == -1:
			success = False
	except pysvn.ClientError as e:
		print e.args
		if len(e.args) >= 2:
			for message, code in e.args[1]:
				print 'Code:',code,'Message:',message
		success = False
	return success


def svn_up_list(pathlist, revision=None, revert=True):
	print 'svn_up_list', pathlist, revision, revert
	success = True
	revision=pysvn.Revision( pysvn.opt_revision_kind.number, revision ) if revision else pysvn.Revision( pysvn.opt_revision_kind.head )

	for i in pathlist:
		#出error或者其他失败原因，都马上中止函数并返回false
		try:
			if revert:
				svn_client_inst.revert(i, True)
			if svn_client_inst.update(i, True, revision) == -1:
				success = False
				break
		except pysvn.ClientError, e:
			print e.args
			for message, code in e.args[1]:
				print 'Code:',code,'Message:',message
			success = False
			break
	return success


def compare_dir_only(src_path, dst_path):
	return filecmp.dircmp(src_path,dst_path)

#比较源文件夹和目标文件夹并自动执行以下功能，
#		对任何文件，如果源文件夹中存在，但目标文件夹中不存在，则copy并add到目标文件夹
#					如果源文件夹和目标文件夹都存在，但两个文件不同，则copy并覆盖到目标文件夹
#					如果源文件中不存在，但目标文件夹中存在，则删掉目标文件夹相应的文件
#param：
#	log_message svn 操作的log_message
#	include_ext_list 包含的后缀名列表，默认不检查
#	exclude_ext_list 剔除的后缀名列表，默认不检查
#返回值：[执行是否成功，比较结果]
def compare_dir_and_do_svn(src_path, dst_path, log_message, include_ext_list=None, exclude_ext_list=None, enable_add=True, enable_remove=True):
	result = compare_dir_only(src_path, dst_path)
	success = True

	#自动处理svn操作
	#如果源文件夹和目标文件夹都存在，但两个文件不同，则copy并覆盖到目标文件夹
	if len(result.diff_files)!=0:
		for file in result.diff_files:
			print "diff_files", file
			ext = os.path.splitext(file)[1][1:]
			if (include_ext_list != None and ext not in include_ext_list) or (exclude_ext_list != None and ext in exclude_ext_list):
				continue
			srcfile=os.path.join(src_path,file)
			shutil.copy(srcfile, dst_path);

	#如果源文件夹中存在，但目标文件夹中不存在，则copy并add到目标文件夹
	if enable_add and len(result.left_only)!=0:
		for file in result.left_only:
			print "left_only",file
			ext = os.path.splitext(file)[1][1:]
			if (include_ext_list != None and ext not in include_ext_list) or (exclude_ext_list != None and ext in exclude_ext_list):
				continue
			srcfile=os.path.join(src_path,file)
			dstfile=os.path.join(dst_path,file)
			shutil.copy(srcfile, dst_path)
			svn_client_inst.add(dstfile)

	#如果源文件中不存在，但目标文件夹中存在，则删掉目标文件夹相应的文件
	if enable_remove and len(result.right_only)!=0:
		for file in result.right_only:
			print "right_only", file
			ext = os.path.splitext(file)[1][1:]
			if (include_ext_list != None and ext not in include_ext_list) or (exclude_ext_list != None and ext in exclude_ext_list):
				continue
			dstfile=os.path.join(dst_path,file)
			svn_client_inst.remove(dstfile)

	try:
		if svn_client_inst.checkin(dst_path, log_message) == -1:
			success = False
	except pysvn.ClientError, e:
		print e.args[0]
		for message, code in e.args[1]:
			print 'Code:',code,'Message:',message
		success = False
	print "compare_dir", "success" if success else "faild"
	return [success, result]




def auto_svn_ci_add_rm(dir_path, log_message, auto_add=True, auto_rm=True):
	"will automatically add && remove && commit files in dir"
	print "auto_svn_ci_add_rm",dir_path,"with log", log_message
	statusList = svn_client_inst.status(dir_path)
	for i in statusList:
		if auto_add and i.text_status == pysvn.wc_status_kind.unversioned:
			svn_client_inst.add(i.path)
		elif auto_rm and i.text_status == pysvn.wc_status_kind.missing:
			svn_client_inst.remove(i.path)
	svn_client_inst.checkin(dir_path, log_message)


#ext_list是文件格式列表如[txt, tps...]
#exclude_list是排除的文件列表，如[xxx.txt, 1.plist]
def find_all_file_in_dir(folder, ext_list=[], exclude_list=[]):
	paths = []
	check_ext = len(ext_list)>0
	check_exclude = len(exclude_list)>0
	for root, dirs, files in os.walk(folder):
		for fn in files:
			if not check_ext or os.path.splitext(fn)[1][1:] in ext_list:
				if not check_exclude or fn not in exclude_list:
					paths.append(os.path.join(root, fn))

	return paths


def file_is_early_than_file(file1, file2):
	pass

def file_is_early_than_time(file, time):
	pass

# 创建branch
def make_branch(src_url, dst_url, log_message, revision=None):
	print "make_branch",src_url," to ", dst_url
	def get_log_message():
		return True, log_message
	svn_client_inst.callback_get_log_message = get_log_message
	revision = pysvn.Revision( pysvn.opt_revision_kind.number, revision ) if revision else pysvn.Revision( pysvn.opt_revision_kind.head )
	svn_client_inst.copy(src_url, dst_url, revision)

def get_head_revision(src_url):
	return svn_client_inst.info2(src_url, pysvn.Revision( pysvn.opt_revision_kind.head ))[0][1].rev.number

# 创建externals, external_props = [(dst_url, external_name, revision), ]
def make_externals(src_parent_url, external_props, log_message):
	print "make_externals on ", src_parent_url
	externals = None
	for external_prop in external_props:
		external = external_prop[0]
		if len(external_prop) >= 3 and external_prop[2] != None:
			external += "@" + str(external_prop[2])
		external += " " + external_prop[1]
		if not externals:
			externals = external
		else:
			externals += "\n" + external
	if externals:
		def get_log_message():
			return True, log_message
		svn_client_inst.callback_get_log_message = get_log_message
		svn_client_inst.propset("svn:externals", externals, src_parent_url, base_revision_for_url=get_head_revision(src_parent_url) )

# 锁定externals的版本, external_props = [(dst_url, external_name, revision), ]
def peg_externals(src_parent_url, external_props, log_message):
	print "peg_externals on ", src_parent_url
	externals = None
	for external_prop in external_props:
		external = external_prop[0]
		if len(external_prop) >= 3 and external_prop[2] != None:
			external += "@" + str(external_prop[2])
		else:
			external += "@" + str(get_head_revision(external_prop[0]))
		external += " " + external_prop[1]
		if not externals:
			externals = external
		else:
			externals += "\n" + external
	if externals:
		def get_log_message():
			return True, log_message
		svn_client_inst.callback_get_log_message = get_log_message
		svn_client_inst.propset("svn:externals", externals, src_parent_url, base_revision_for_url=get_head_revision(src_parent_url) )

def get_external_revision(src_parent_url):
	prop_list = svn_client_inst.propget("svn:externals", src_parent_url)
	return prop_list.values()[0].split(' ')[0].split('@')

# 复制目录的external作为branch
def copy_external(src_parent_url, dst_url, log_message):
	print "copy_external on ", src_parent_url
	prop = get_external_revision(src_parent_url)
	revision=None
	if len(prop) >= 2:
		revision = prop[1]
	make_branch(prop[0], dst_url, log_message, revision)

def svn_del(src_url, log_message):
	print "svn_del ", src_url
	def get_log_message():
		return True, log_message
	svn_client_inst.callback_get_log_message = get_log_message
	svn_client_inst.remove(src_url)

def svn_mkdir(src_url_or_list, log_message):
	print "svn_mkdir ", str(src_url_or_list)
	svn_client_inst.mkdir(src_url_or_list, log_message)

def svn_merge(start_url_or_path, start_revision, end_url_or_path, end_revision, local_path):
	print "svn_merge"
	svn_client_inst.merge(start_url_or_path, pysvn.Revision( pysvn.opt_revision_kind.number, start_revision ), end_url_or_path, pysvn.Revision( pysvn.opt_revision_kind.number, end_revision ), local_path)

if __name__ == '__main__':
	if len(sys.argv)==4:
		svn_up_list([sys.argv[2]], None, True)
		compare_dir_and_do_svn(sys.argv[1], sys.argv[2], sys.argv[3])

	if len(sys.argv)==2:
		svn_up_list([sys.argv[1]])

def copy_external_prop(src_parent_url, dst_parent_url, log_message):
	prop_list = svn_client_inst.propget("svn:externals", src_parent_url)
	def get_log_message():
		return True, log_message
	svn_client_inst.callback_get_log_message = get_log_message
	svn_client_inst.propset("svn:externals", prop_list.values()[0], dst_parent_url, base_revision_for_url=get_head_revision(dst_parent_url) )
