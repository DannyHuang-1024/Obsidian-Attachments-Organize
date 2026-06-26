import os
import re
import shutil
import stat
from pathlib import Path


class Process:
    def __init__(self, project_path, attachments_dir_name="attachments"):
        self.project_root = self.check_path(project_path)
        self.project_path = self.project_root
        self.list_of_md_files = []
        self.attachments = []
        self.copied_flag = False
        self._protected_attachment_paths = set()
        self.att_dir_name = attachments_dir_name
        self._attachments_by_relpath = {}
        self._attachments_by_name = {}
        self.get_list_of_files(self.project_root)

    def check_path(self, path):
        p = Path(path).expanduser()
        if p.exists() and p.is_dir():
            return p.resolve()
        raise ValueError("The project path is not valid! Please check!!!")

    def _relative_attachment_key(self, attachment: Path) -> str:
        try:
            return attachment.relative_to(self.project_root).as_posix()
        except ValueError:
            return attachment.as_posix()

    def _refresh_attachment_indexes(self) -> None:
        self._attachments_by_relpath = {}
        self._attachments_by_name = {}
        for attachment in self.attachments:
            rel_key = self._relative_attachment_key(attachment)
            self._attachments_by_relpath.setdefault(rel_key, []).append(attachment)
            self._attachments_by_name.setdefault(attachment.name, []).append(attachment)

    def _build_attachment_indexes(self, attachments_list):
        by_relpath = {}
        by_name = {}
        for attachment in attachments_list:
            rel_key = self._relative_attachment_key(attachment)
            by_relpath.setdefault(rel_key, []).append(attachment)
            by_name.setdefault(attachment.name, []).append(attachment)
        return by_relpath, by_name

    def _normalize_embed_target(self, target: str) -> str:
        target = target.strip().replace("\\", "/")
        if target.startswith("./"):
            target = target[2:]
        if "#" in target:
            target = target.split("#", 1)[0]
        if "^" in target:
            target = target.split("^", 1)[0]
        return target

    def _resolve_attachment_matches(self, target: str, md_file: Path, attachments_list):
        normalized = self._normalize_embed_target(target)
        if not normalized:
            return []

        by_relpath, by_name = self._build_attachment_indexes(attachments_list)
        exact_matches = by_relpath.get(normalized, [])
        if exact_matches:
            return exact_matches

        basename = Path(normalized).name
        candidates = by_name.get(basename, [])
        if len(candidates) <= 1:
            return candidates

        note_dir = md_file.parent.resolve()
        preferred = [
            attachment
            for attachment in candidates
            if attachment.parent == note_dir or attachment.parent == note_dir / self.att_dir_name
        ]
        if preferred:
            return preferred

        return candidates

    def get_list_of_files(self, directory) -> tuple[list[Path], list[Path]]:
        """
        Return the list of Markdown files and attachment files under `directory`.
        Hidden directories and hidden files are skipped.
        """
        directory = Path(directory)
        self.list_of_md_files = []
        self.attachments = []

        for root, dirs, files in os.walk(directory):
            # Don't enter hidden directories.
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                if file.startswith("."):
                    continue

                path = Path(root) / file
                ext = self.get_real_extension(path)

                if path.suffix == ".md" and ext != "excalidraw":
                    self.list_of_md_files.append(path)
                else:
                    self.attachments.append(path)

        self._refresh_attachment_indexes()
        return self.list_of_md_files, self.attachments

    def get_real_extension(self,path: str) -> str | None:
        suffixes = Path(path).suffixes
        if len(suffixes) >= 2:
            return suffixes[-2].lstrip(".")
        if len(suffixes) == 1:
            return suffixes[0].lstrip(".")
        return None

    def ensure_attachments_dir(self, path: str, dir_name: str) -> None:
        Path(path, dir_name).mkdir(parents=True, exist_ok=True)


    def read_md_files(self, path_md_file, attachments_list):
        """
        This function is used to read md file and find all attachments labels in it
        
        return : list[(string, string)]     
            The first element in the tuple is only the attachment file name(with file extension)
            The second element in the tuple is the whole path of the attachment
        """
        pattern = r"!\[\[([^\]\|]+)(?:\|(\d+))?\]\]"
        with open(path_md_file, "r", encoding="utf-8") as f:
            text = f.read()
        
        attachments_in_md = []

        for m in re.finditer(pattern, text):
            file = m.group(1)
            if Path(file).suffix == ".excalidraw":
                file = f"{file}.md"

            for att in self._resolve_attachment_matches(file, Path(path_md_file), attachments_list):
                if att not in attachments_in_md:
                    attachments_in_md.append(att)

        return attachments_in_md


    def copy_attachments(self):
        if self.list_of_md_files == []:
            return False
        self._protected_attachment_paths = set()
        list_of_md_files, list_of_attachments = self.list_of_md_files, self.attachments
        for md_file in list_of_md_files:
            attachments_in_md = self.read_md_files(md_file, list_of_attachments)
            current_dir = md_file.parent
            self.ensure_attachments_dir(current_dir, self.att_dir_name)
            for attachment_path in attachments_in_md:
                target_path = current_dir / self.att_dir_name / attachment_path.name
                self._protected_attachment_paths.add(target_path.resolve())
                if target_path.exists():
                    continue
                shutil.copy2(attachment_path, target_path)

        self.copied_flag = True
        return True
    
    def rescan(self):
        self.get_list_of_files(self.project_path)


    def remove(self):
        """
        Copy referenced attachments into the configured attachment folders,
        delete unreferenced attachments, and remove empty directories.
        """
        if not self.copy_attachments():
            return {
                "removed_attachments": 0,
                "removed_directories": 0,
                "failed_directories": [],
            }

        self.rescan()
        removed_attachments = self.remove_unused_attachments()
        removed_dirs, failed_dirs = self.remove_empty_directories()
        self.copied_flag = False
        return {
            "removed_attachments": removed_attachments,
            "removed_directories": removed_dirs,
            "failed_directories": failed_dirs,
        }

    def remove_unused_attachments(self):
        """
        This function will delete all the attachments that not appear in md files.
        So be careful while using it
        """
        list_of_md_files, all_attachments = self.list_of_md_files, self.attachments

        used_attachment_paths = set()

        for md_file in list_of_md_files:
            attachments_in_md = self.read_md_files(md_file, all_attachments)
            for attachment in attachments_in_md:
                used_attachment_paths.add(attachment.resolve())
        
        removed = 0

        for attachment in all_attachments[:]:
            path = Path(attachment)
            resolved = path.resolve()
            if resolved in self._protected_attachment_paths:
                continue
            if resolved not in used_attachment_paths:
                removed += 1
                path.unlink(missing_ok=True)
                all_attachments.remove(attachment)
            elif self.copied_flag and path.parent.name != self.att_dir_name:
                path.unlink(missing_ok=True)
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
        failed = []
        protected_names = {".git", ".obsidian"}

        for root, dirs, files in os.walk(top, topdown=False, onerror=lambda e: None):
            root_path = Path(root)
            if root_path == top or root_path.name.startswith(".") or root_path.name in protected_names:
                continue

            for junk in ("desktop.ini", "Thumbs.db"):
                jp = root_path / junk
                if jp.exists() and jp.is_file():
                    try:
                        self._try_make_writable(jp)
                        jp.unlink()
                    except Exception:
                        pass

            if root_path == top:
                continue

            try:
                root_path.rmdir()
                removed += 1
            except PermissionError as e:
                self._try_make_writable(root_path)
                try:
                    root_path.rmdir()
                    removed += 1
                except Exception as e2:
                    failed.append((str(root_path), repr(e2)))
            except OSError:
                # Not empty: this is expected for folders that still contain
                # referenced attachments or other content.
                continue

        return removed, failed
