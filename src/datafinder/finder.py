import pandas as pd
import pathlib as pl
import re

class DataFinder:
    """
    DataFinder is a utility class for searching and extracting information from files in specified folders.
    It supports recursive search and regex-based extraction of metadata from file paths.
    """

    def __init__(self, folders=[], root="."):
        """
        Initialize the DataFinder with a list of folders and a root directory.
        Args:
            folders (list): List of folder paths to search in.
            root (str or Path): The root directory for relative paths.
        """
        self.folders = []
        self.add_folders(folders, root)

    def set_root(self, root):
        """
        Set the root directory for the DataFinder.
        Args:
            root (str, Path, or list): The root directory to set. If a list is provided, the first valid directory is used.
        Raises:
            ValueError: If the root (or none of the provided roots) does not exist or is not a directory.
        Note:
            If a list of roots is provided, the first valid directory in the list will be used as the root.
        """
        if isinstance(root, list):
            valid_roots = [pl.Path(r) for r in root if pl.Path(r).is_dir()]
            if not valid_roots:
                raise ValueError("None of the provided roots exist or are directories.")
            self.root = valid_roots[0]  # Use the first valid root
        else:
            root = pl.Path(root)
            if not root.is_dir():
                raise ValueError(f"Root {root} does not exist or is not a directory.")

        self.root = root

    def add_folders(self, folders, root=None, strict=False):
        """
        Add folders to the search list. Optionally set a new root directory.
        Args:
            folders (list): List of folder paths to add.
            root (str or Path, optional): New root directory.
            strict (bool): If True, raise error if folder does not exist.
        Raises:
            ValueError: If strict is True and a folder does not exist.
        """
        if root is not None:
            self.set_root(root)

        for folder in folders:
            folder = pl.Path(folder)
            if not folder.is_absolute():
                folder = self.root / folder

            if not folder.is_dir():
                if strict:
                    raise ValueError(
                        f"Folder {folder} does not exist or is not a directory."
                    )
                else:
                    print(
                        f"Warning: Folder {folder} does not exist or is not a directory. Skipping."
                    )
                    continue

            self.folders.append(folder)

    def query(self, query, regex_info={}, require_match=True, verbose=False):
        """
        Search for files matching a pattern and extract metadata using regex.
        Args:
            query (str): Glob pattern for file search (e.g., '*.tif').
            regex_info (dict): Mapping of path part indices to regex patterns for metadata extraction.
            require_match (bool): If True, only keep files matching all regexes.
            verbose (bool): If True, print detailed search progress.
        Returns:
            pd.DataFrame: DataFrame with file info and extracted metadata.
        """
        if verbose:
            print("Searching for files matching:", query)
            print("In root folder:", self.root)


        rows = []
        for folder in self.folders:

            if verbose:
                print("  Entering folder:", folder.relative_to(self.root))

            files = pl.Path(folder).rglob(query)

            for file in files:

                if verbose:
                    print("    Found file:", file.relative_to(self.root), end="")

                row = {"filename": file.name, "path": file, "suffix": file.suffix}

                keep = True
                # Iterate over path parts in reverse for regex extraction
                parts = file.relative_to(self.root).parts

                regex_info_mod = {i % len(parts) : reg for (i, reg) in regex_info.items() }
                for i, part in enumerate(reversed(parts)):

                    if i in regex_info_mod.keys():
                        if type(regex_info_mod[i]) is dict:
                            # If regex_info[i] is a dict, use it to update the row
                            for key, regex in regex_info_mod[i].items():
                                m = re.match(regex, part)
                                if m is not None:
                                    row["info"] = key
                        else:
                            m = re.match(regex_info_mod[i], part)
                            if m is not None:
                                row.update(m.groupdict())
                            else:
                                if require_match:
                                    keep = False

                if keep:
                    rows.append(row)

                if verbose:
                    if not keep and not require_match:
                        print(" \t- No regex match required, keeping file.")
                    if keep:
                        print(" \t- Match found!")
                    else:
                        print(" \t- No match found, skipping file.")

        if len(rows) == 0:
            if verbose:
                print("No files found matching the query.")
            return pd.DataFrame()

        df = pd.DataFrame(rows).sort_values(by="filename").reset_index(drop=True)

        return df