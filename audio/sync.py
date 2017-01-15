import os
import filecmp
import shutil
from stat import *
from threading import Thread

class Sync(Thread):
    def __init__(self, name=''):
        Thread.__init__(self)
        self.name = name
        self.folder_list = []

    def run(self):
        self.compare_folders()

    def add_folder(self, folder):
        self.folder_list.append(folder)

    def compare_folders(self):
        folderListLength = len(self.folder_list)
        # For each folder in the list
        for folder in self.folder_list:
            # If the list has another item after it, compare them
            if self.folder_list.index(folder) < len(self.folder_list) - 1: 
                folder2 = self.folder_list[self.folder_list.index(folder) + 1]

                # Passes the two root directories of the folders to the recursive _compare_directories.
                self._compare_directories(folder.root_path, folder2.root_path)
    
    def _compare_directories(self, left, right):
        # This method compares directories. If there is a common directory, the
        # algorithm must compare what is inside of the directory by calling this
        #  recursively.
        comparison = filecmp.dircmp(left, right)
        if comparison.common_dirs:
            for d in comparison.common_dirs:
                self._compare_directories(os.path.join(left, d), os.path.join(right, d))
        
        if comparison.left_only:
            self._remove(comparison.left_only, left)
        
        if comparison.right_only:
            self._copy(comparison.right_only, right, left)
        
        left_newer = []
        right_newer = []
        
        if comparison.diff_files:
            for d in comparison.diff_files:
                l_modified = os.stat(os.path.join(left, d)).st_mtime
                r_modified = os.stat(os.path.join(right, d)).st_mtime
                if l_modified > r_modified:
                    left_newer.append(d)
                else:
                    right_newer.append(d)
        
        self._copy(left_newer, left, right)
        self._copy(right_newer, right, left)

    def _copy(self, file_list, src, dest):
        # This method copies a list of files from a source node to a destination node
        for f in file_list:
            srcpath = os.path.join(src, os.path.basename(f))
            if os.path.isdir(srcpath):
                shutil.copytree(srcpath, os.path.join(dest, os.path.basename(f)))
            else:
                shutil.copy2(srcpath, dest)

    def _remove(self, file_list, src):
        for f in file_list:
            srcpath = os.path.join(src, os.path.basename(f))
            if os.path.isdir(srcpath):
                shutil.rmtree(srcpath)
            else:
                os.remove(srcpath)


class Folder():
    # This class represents a folder in a Load synchronization '''  
    def __init__(self, path, name=''):
        self.name = name
        self.root_path = os.path.abspath(path)
        self.file_list = os.listdir(self.root_path)