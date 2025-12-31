import os
import re
import shutil
from pathlib import Path

def get_list_of_files(directory) -> tuple[list[str], list[str]]:
    """
    Returns a list of all files in the given directory.
    directory: string
    """
    list_of_attachments = []
    list_of_attachments_path = []
    list_of_md_files = []


    for root, dirs, files in os.walk(directory):
        '''
        root: the path to the directory which is traversing now -> string
        dirs: the directories directly inside the root now -> list
        files: the files directly inside the root now -> list 
        '''

        for file in files:
            path = os.path.join(root, file)
            if file.endswith(".md"):
                list_of_md_files.append(path)
            else:
                list_of_attachments_path.append(path)
                list_of_attachments.append(file)

        attachments = [(x, y) for x,y in zip(list_of_attachments, list_of_attachments_path)]        
    
    return list_of_md_files, attachments


def ensure_dir(path: str, dir_name: str) -> None:
    # This function is used to make sure the "attachments" directory exists 
    # if not, then create it
    attachments_path = os.path.join(path, dir_name)
    os.makedirs(attachments_path, exist_ok=True)

def read_md_files(path_md_file, attachments_list):
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
            print(file)
        for att in attachments_list:
            if(att[0] == file):
                attachments_in_md.append((att[0], att[1]))
    
    return attachments_in_md


def copy_attachments(project_path: str):
    list_of_md_files, list_of_attachments = get_list_of_files(project_path)
    for md_file in  list_of_md_files :
        attachments_in_md = read_md_files(md_file, list_of_attachments)
        current_dir = os.path.dirname(md_file)
        ensure_dir(current_dir, "attachments")
        for attachment_name, attachment_path in attachments_in_md:
            
            # attachment_path is got from read_md_file
            # it is the path directly point the real attachment file
            if os.path.exists(
                os.path.join(current_dir,"attachments", attachment_name)
            ): continue
            else:
                target_path = os.path.join(current_dir, "attachments", attachment_name)
                # shutil.copy2(attachment_path, target_path)
