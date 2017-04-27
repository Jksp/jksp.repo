#!/usr/bin/env python
# *
# *  Copyright (C) 2017      jk$p
# *  Copyright (C) 2012-2013 Garrett Brown
# *  Copyright (C) 2010      j48antialias
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  Based on code by j48antialias:
# *  https://anarchintosh-projects.googlecode.com/files/addons_xml_generator.py
 
""" addons.xml generator """

import errno
import re
import os
import subprocess
import sys
import zipfile
 
# Compatibility with 3.0, 3.1 and 3.2 not supporting u"" literals
if sys.version < '3':
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x
 
class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from the root of
        the checked-out repo. Only handles single depth folder structure.
    """

    excluded_folders = {'.svn': '.svn', '.git': '.git', 'repo': 'repo'}
    excluded_files = {'thumbs.db': 'thumbs.db', 'desktop.ini': 'desktop.ini'}

    def __init__(self, src_folder, repo_folder):
        self.src_folder = os.path.join(src_folder, "")
        self.repo_folder = os.path.join(repo_folder, "")

    def generate_repo(self):
        # generate files
        self._generate_addons_zips()
        self._generate_addons_xml_file()
        self._generate_addons_xml_md5_file()

    def _generate_addons_zips(self):
        # addon list
        addons = os.listdir(self.src_folder + ".")

        # loop thru and add each addons files to zip
        for addon in addons:
            addon_path = os.path.join(self.src_folder, addon)
            # skip any .svn folder or .git folder
            if not os.path.isdir(addon_path) or self.excluded_folders.has_key(addon):
                print("Skipped %s" % addon_path)
                continue

            # Get addon version from addon.xml
            addon_version = re.search(r'<addon .+?version="([\d\.]+?)".+?>',
                                      self._read_file(os.path.join(addon_path, "addon.xml")), re.S).group(1)

            zip_name = "%s-%s.zip" % (addon, addon_version)
            zip_path = os.path.join(self.repo_folder, "zips", addon)
            zip_full_path = os.path.join(zip_path, zip_name)

            # make sure destination directory exist
            try:
                os.makedirs(zip_path)
            except OSError as e:
                if e.errno == errno.EEXIST and os.path.isdir(zip_path):
                    pass
                else:
                    print("An error occurred creating directory %s!\n%s" % (zip_path, e))

            if os.path.isfile(zip_full_path):
                print("Skipped %s, already exists!" % zip_name)
                continue

            # create the zip file
            try:
                zip = zipfile.ZipFile(zip_full_path, "w", zipfile.ZIP_DEFLATED)
                for root, dirs, files in os.walk(addon_path):
                    for file in files:
                        # skip any ignored file
                        if self.excluded_files.has_key(file):
                            print("Skipped %s" % os.path.join(root, file))
                            continue

                        zip.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), self.src_folder))
                zip.close()

            except Exception as e:
                # oops
                print("An error occurred creating addon zip file %s!\n%s" % (zip_name, e))

    def _generate_addons_xml_file(self):
        # addon list
        addons = os.listdir(self.src_folder + ".")
        
        # final addons text
        addons_xml = u("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\r\n<addons>\r\n")
        # loop thru and add each addons addon.xml file
        for addon in addons:
            _path = os.path.join(self.src_folder, addon)
            # skip any file or .svn folder or .git folder
            if not os.path.isdir(_path) or self.excluded_folders.has_key(addon):
                print("Skipped %s" % _path)
                continue

            # create path
            _path = os.path.join(_path, "addon.xml")
            try:
                # split lines for stripping
                xml_lines = self._read_file(_path).splitlines()

                # new addon
                addon_xml = ""
                # loop thru cleaning each line
                for line in xml_lines:
                    # skip encoding format line
                    if line.find("<?xml") >= 0:
                        continue

                    # add line
                    if sys.version < '3':
                        addon_xml += unicode(line.rstrip() + "\r\n", "UTF-8")
                    else:
                        addon_xml += line.rstrip() + "\r\n"

                # we succeeded so add to our final addons.xml text
                addons_xml += addon_xml.rstrip() + "\r\n\r\n"

            except Exception as e:
                # missing or poorly formatted addon.xml
                print("Excluding %s for %s" % (_path, e))

        # clean and add closing tag
        addons_xml = addons_xml.strip() + u("\r\n</addons>\r\n")

        # save file
        self._save_file(addons_xml.encode("UTF-8"), file=os.path.join(self.repo_folder, "addons.xml"))
 
    def _generate_addons_xml_md5_file(self):
        # create a new md5 hash
        try:
            import md5
            m = md5.new(self._read_file(os.path.join(self.repo_folder, "addons.xml"))).hexdigest()
        except ImportError:
            import hashlib
            m = hashlib.md5(self._read_file(os.path.join(self.repo_folder, "addons.xml")).encode("UTF-8")).hexdigest()
 
        # save file
        try:
            self._save_file(m.encode("UTF-8"), file=os.path.join(self.repo_folder, "addons.xml.md5"))

        except Exception as e:
            # oops
            print("An error occurred creating addons.xml.md5 file!\n%s" % e)
 
    def update_git(self, git_repo, git_executable):
        if git_executable is None:
            git_executable = self._which("git.exe" if os.name == "nt" else "git")

        if git_executable is None or not self._is_executable(git_executable):
            print("Could not find Git executable")
            return

        out, err = subprocess.Popen([git_executable, "add", "-v", os.path.join(os.path.abspath(self.repo_folder), "*")],
                                    bufsize=-1,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    cwd=git_repo).communicate()
        if err:
            print("Git returned error: %s" % err)

    def _read_file(self, file):
        try:
            # read data to from file
            with open(file, "r") as f:
                return f.read()
        except Exception as e:
            # oops
            print("An error occurred reading %s file!\n%s" % (file, e))
            return ""

    def _save_file(self, data, file):
        try:
            # write data to the file (use b for Python 3)
            with open(file, "wb") as f:
                f.write(data)
        except Exception as e:
            # oops
            print("An error occurred saving %s file!\n%s" % (file, e))

    def _which(self, program):
        # like the unix command which
        fpath, fname = os.path.split(program)
        if fpath:
            if self._is_executable(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if self._is_executable(exe_file):
                    return exe_file

        return None

    def _is_executable(self, filename):
        return os.path.isfile(filename) and os.access(filename, os.X_OK)
 
 
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("%s <src_dir> <repo_dir> [git_repository_dir] [path_to_git_executable]" % os.path.basename(sys.argv[0]))
        exit(-1)

    # start
    generator = Generator(sys.argv[1], sys.argv[2])
    generator.generate_repo()
    if len(sys.argv) > 3:
        generator.update_git(sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)

    # notify user
    print("Finished updating repo")
