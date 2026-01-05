import os
import re
import shutil
import stat
from pathlib import Path

class Process():
    def __init__(self, project_path, attachments_dir_name="attachments"):

        if self.check_path(project_path):
            # If the path is correct
            self.project_path = project_path    
            self.list_of_md_files = []
            self.attachments = []
            self.copied_flag = False

            self.att_dir_name = attachments_dir_name

            # Init Process
            self.get_list_of_files(self.project_path)

    def check_path(self, path):
        p = Path(path)
        exists = p.exists()
        is_dir = p.is_dir()

        if exists and is_dir:
            self.project_path = path
            return True
        else:
            raise ValueError("The project path is not valid! Please check!!!")


    def get_list_of_files(self, directory) -> tuple[list[str], list[(str, str)]]:
        """
        Returns a list of all files in the given directory.
        directory: string

        return: 
            the first return is the list of all md_files(Whole path)
            the second return is the list of (attachment_name, attachment_path)
        """
        list_of_attachments = []
        list_of_attachments_path = []


        for root, dirs, files in os.walk(directory):
            '''
            root: the path to the directory which is traversing now -> string
            dirs: the directories directly inside the root now -> list
            files: the files directly inside the root now -> list 
            '''

            # Don't enter hidden directories (prune traversal)
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                path = os.path.join(root, file)
                ext = self.get_real_extension(path)

                if file.endswith(".md") and ext != 'excalidraw':
                    self.list_of_md_files.append(path)
                else:
                    list_of_attachments_path.append(path)
                    list_of_attachments.append(file)

            self.attachments = [(x, y) for x,y in zip(list_of_attachments, list_of_attachments_path)]        
        
        return self.list_of_md_files, self.attachments

    def get_real_extension(self,path: str) -> str | None:
        suffixes = Path(path).suffixes
        if len(suffixes) >= 2:
            return suffixes[-2].lstrip(".")
        if len(suffixes) == 1:
            return suffixes[0].lstrip(".")
        return None

    def ensure_attachments_dir(self, path: str, dir_name: str) -> None:
        # This function is used to make sure the "attachments" directory exists 
        # if not, then create it
        attachments_path = os.path.join(path, dir_name)
        os.makedirs(attachments_path, exist_ok=True)


    def read_md_files(self, path_md_file, attachments_list):
        """
        This function is used to read md file and find all attachments labels in it
        
        return : list[(string, string)]     
            The first element in the tuple is only the attachment file name(with file extension)
            The second element in the tuple is the whole path of the attachment
        """
        pattern = r"!\[\[([^\]\|]+)(?:\|(\d+))?\]\]"
        text = ""

        with open(path_md_file, "r", encoding="utf-8") as f:
            text = f.read()
        
        attachments_in_md = []

        for m in re.finditer(pattern, text):
            file = m.group(1) # 1 catch the file and 2 catch the resized number
            
            ext = Path(file).suffix
            if ext == ".excalidraw":
                file = file + ".md"
            for att in attachments_list:
                if(att[0] == file) and (att[0], att[1]) not in attachments_in_md:
                    # One attachment link in a md file only store once
                    attachments_in_md.append((att[0], att[1]))

        return attachments_in_md


    def copy_attachments(self):
        if self.list_of_md_files == []:
            return False
        list_of_md_files, list_of_attachments = self.list_of_md_files, self.attachments
        for md_file in  list_of_md_files :
            attachments_in_md = self.read_md_files(md_file, list_of_attachments)
            current_dir = os.path.dirname(md_file)
            self.ensure_attachments_dir(current_dir, self.att_dir_name)
            for attachment_name, attachment_path in attachments_in_md:
                
                # attachment_path is got from read_md_file
                # it is the path directly point the real attachment file
                if os.path.exists(
                    os.path.join(current_dir, self.att_dir_name, attachment_name)
                ): continue
                else:
                    target_path = os.path.join(current_dir, self.att_dir_name, attachment_name)
                    shutil.copy2(attachment_path, target_path)

        self.copied_flag = True
        return True
    
    def rescan(self):
        self.list_of_md_files = []
        self.attachments = []
        self.get_list_of_files(self.project_path)


    def remove(self):
        """
        Use some trick to remove unused attachments that are in the specified atts's dir
        1. First move all used attachments to a special dir
        2. Then remove all attachments in the original attachments dir(So the unused attachments are removed)
        3. Finally move back all used attachments to the original attachments dir
        """

        temp_name = self.att_dir_name
        self.att_dir_name = "temp_attachments_dir_for_removal"
        self.copy_attachments() # Copy all used attachments to temp dir
        self.rescan() # Rescan the project to update the attachments list

        # Remove all unused attachments in the original attachments dir
        self.remove_unused_attachments()
        self.remove_empty_directories()

        # Move back all used attachments to the original attachments dir
        self.att_dir_name = temp_name
        self.rescan()
        self.copy_attachments()
        self.rescan()

        # Finally remove the temp dir and its empty parent dirs
        self.remove_unused_attachments()
        self.remove_empty_directories()

    def remove_unused_attachments(self):
        """
        This function will delete all the attachments that not appear in md files.
        So be careful while using it
        """
        list_of_md_files, all_attachments = self.list_of_md_files, self.attachments


        hash_of_attachments = {}

        for md_file in  list_of_md_files :
            attachments_in_md = self.read_md_files(md_file, all_attachments)
            for attachment in attachments_in_md:
                name = attachment[0] # Only storage the name of the file, without path
                hash_of_attachments[name] = hash_of_attachments.get(name,0) +1
        
        removed = 0

        for attachment in all_attachments[:]:
            # Use a copy of the list to iterate
            # Because we will delete some elements from the original list
            att_name = attachment[0]
            path = Path(attachment[1])
            # print("removed: " + att_name)

            if att_name not in hash_of_attachments:
                '''
                This judge is to delete the attachments exists in project
                but never used
                '''
                removed += 1
                path.unlink()
                all_attachments.remove(attachment)
                # print("File removed : {}".format(path))
            
            elif self.copied_flag:
                '''
                This judge is to delete the repeat attachments
                that are moved to new attachments files
                '''
                if path.parent.name != self.att_dir_name :
                    path.unlink()
                    all_attachments.remove(attachment)
        return removed

    def _try_make_writable(self, p: Path) -> None:
        """Best-effort: remove read-only attribute (mostly useful for files on Windows)."""
        try:
            os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass

    def remove_empty_directories(self):
        top = Path(self.project_path)
        removed = 0
        failed = []  # collect failures so you can debug

        # Walk bottom-up (safer than rglob: avoids crashing on permission-troubled dirs)
        for root, dirs, files in os.walk(top, topdown=False, onerror=lambda e: None):
            root_path = Path(root)

            # Optional: if you want to skip deleting anything under special dirs
            # (uncomment if needed)
            # if root_path.name in {".obsidian", ".git"}:
            #     continue

            # Remove common Windows junk files that prevent "empty" dirs
            for junk in ("desktop.ini", "Thumbs.db"):
                jp = root_path / junk
                if jp.exists() and jp.is_file():
                    try:
                        self._try_make_writable(jp)
                        jp.unlink()
                    except Exception:
                        pass

            for dname in dirs:
                d = root_path / dname
                try:
                    d.rmdir()
                    removed += 1
                except PermissionError as e:
                    # try again after making writable (best-effort)
                    self._try_make_writable(d)
                    try:
                        d.rmdir()
                        removed += 1
                    except Exception as e2:
                        failed.append((str(d), repr(e2)))
                except OSError as e:
                    # not empty, or other issue
                    failed.append((str(d), repr(e)))

        return removed, failed