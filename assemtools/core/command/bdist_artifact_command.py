# -*- coding:utf-8 -*-
#!/usr/bin/env python
# type: ignore

import sys, os, re, zipfile, shutil, subprocess, glob, datetime, csv, subprocess
from sysconfig import get_python_version
from distutils import log
from distutils.core import Command
from distutils.dist import Distribution
# from distutils.command import bdist
# from setuptools import Command
# from pip import main as pip_main
# from pip._internal.cli.main import main as pip_main
from ...utility.pkg import cov_to_safer_package_name, cov_to_safer_package_version, cov_to_app_name, write_installer

class bdist_artifact(Command):
    description = 'Create an artifact'

    user_options = [
        ('binary', None, "Do not use source packages. Can be supplied multiple times, and each time adds to the existing value. Accepts either :all: to disable all source packages, :none: to empty the set, or one or more package names with commas between them. Packages without binary distributions will fail to install when this option is used on them."),
        ('pre', None, "Include pre-release and development versions. By default, pip only finds stable versions."),
        ('rpm', None, 'Make rpm artifact'),
        ('deb', None, 'Make deb artifact'),
        ('index-url=', 'i', "Base URL of the Python Package Index (default https://mirrors.aliyun.com/pypi/simple). This should point to a repository compliant with PEP 503 (the simple repository API) or a local directory laid out in the same format"),
        ('trusted-host=', 'h', "Mark this host or host:port pair as trusted, even though it does not have valid or any HTTPS"),
        ('plugin=', None, 'The artifact plugin module. Split with \':\'.')
    ]

    boolean_options = [
        'binary',
        'pre',
        'rpm',
        'deb'
    ]

    def __init__(self, dist: Distribution) -> None:
        super().__init__(dist)

    def initialize_options(self):
        self.binary = None
        self.pre = None
        self.index_url = None
        self.trusted_host = None
        self.dist_dir = None
        self.bdist_building_dir = None
        # self.pip_buiding_dir = None
        self.rpm = None
        self.deb = None
        self.plugin = None

    def finalize_options(self):
        bdist_base = self.get_finalized_command('bdist').bdist_base
        self.bdist_building_dir = os.path.join(bdist_base, 'bdist_artifact')
        # self.pip_buiding_dir = os.path.join(bdist_base, 'pip_building')

        self.set_undefined_options('bdist', ("dist_dir", "dist_dir"))

        # print('1'*30, self.egginfo_dir, self.get_finalized_command('install_egg_info').get_outputs())

    def __make_rpm_artifact(self, app_archive:str):
        # Get archive file path 
        # app_rpm_artifact = os.path.join(self.dist_dir, "%s-%s.rpm" % (
        #     cov_to_safer_package_name(self.distribution.get_name()),
        #     cov_to_safer_package_version(self.distribution.get_version())
        # ))
        app_name = cov_to_app_name(self.distribution.get_name())

        # Make work directory
        work_dir = os.path.join(self.bdist_building_dir, 'rpm')
        rpmbuild_dir = os.path.abspath(os.path.join(work_dir, 'RPMBUILD'))
        build_dir = os.path.join(rpmbuild_dir, 'BUILD')
        rpms_dir = os.path.join(rpmbuild_dir, 'RPMS')
        srpms_dir = os.path.join(rpmbuild_dir, 'SRPMS')
        sources_dir = os.path.join(rpmbuild_dir, 'SOURCES')
        specs_dir = os.path.join(rpmbuild_dir, 'SPECS')

        spec_string='\n'.join([
        f"%define app_prefix %{{_prefix}}/local/lib/%{{name}}",

        f"Name: {app_name}",
        f"Version: {cov_to_safer_package_version(self.distribution.get_version())}",
        f"Release: 1",

        f"Group: Applications/Internet",
        f"License: {self.distribution.get_license()}",
        f"URL: {self.distribution.get_url()}",
        f"Source0: {os.path.basename(app_archive)}",
        # "BuildArch: noarch" if not self.distribution.has_ext_modules() else f"BuildArch: %s" % self.force_arch
        f"BuildRoot: %{{_tmppath}}/%{{name}}-%{{version}}-%{{release}}-buildroot'",
        f"Prefix: %{{app_prefix}}",
        f"Summary: {self.distribution.get_description()}",

        f"%description",
        f"{self.distribution.get_long_description()}",

        #在执行rpm时完成相关文件资源的预处理
        f"%prep",
        f"%setup -q -c -n %{{name}}",

        f"%build",
        # f"{sys.executable} -c 'import zipfile; z = zipfile.ZipFile(\"%{{SOURCE0}}\", \"r\"); z.extractall(\".\"); z.close()'",

        f"%pre",
 
        f"%install",
        f"mkdir -p %{{buildroot}}/%{{app_prefix}}",
        f"cd %{{_builddir}}/%{{name}}",
        f"find %{{_builddir}}/ -type f -exec install -Dv {{}} %{{buildroot}}%{{app_prefix}}/{{}} \\;",
        f"cd -",

        f"%post",
        f"install_dir=`rpm -ql %{{name}}-%{{version}} | sort | head -1`",
        f"app_dir=\"${{install_dir}}/root\"",
        f"${{install_dir}}/install --prefix ${{app_dir}}",
        f"${{app_dir}}/bin/{app_name}-c-enable-on-systemd",

        f"%clean",

        f"%preun",

        f"%postun",
        f"install_dir=`rpm -ql %{{name}}-%{{version}} | sort | head -1`",
        f"app_dir=\"${{install_dir}}/root\"",
        f"${{app_dir}}/bin/{app_name}-c-disable-on-systemd",
        f"rm -rf ${{app_dir}}",

        f"%files",
        f"%license LICENSE",
        f"%defattr(-,root,root)",
        f"%{{app_prefix}}",

        f"%doc",

        f"%changelog"])

        for d in rpmbuild_dir, build_dir, rpms_dir, srpms_dir, sources_dir, specs_dir:
            os.makedirs(d, exist_ok=True)

        spec_filepath = os.path.join(specs_dir, f'{app_name}.spec')
        with open(spec_filepath, 'w', encoding='utf-8') as f:
            f.write(spec_string)

        # with open(os.path.join(sources_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
        #     f.write('\n'.join(get_installing_requirements())))

        shutil.copy(app_archive, sources_dir)

        subprocess.call(f'rpmbuild --clean -bb {spec_filepath} --define "_topdir {rpmbuild_dir}"', shell=True)

        # rpm_artifact = subprocess.getoutput(f'find {rpmbuild_dir} -path "*RPMS*" -iname *.rpm').strip()
        # if not rpm_artifact:
        #     raise RuntimeError("No rpm artifact")

        # subprocess.call(f'cp -vf {rpm_artifact} {self.dist_dir}', shell=True)

        # return f'{self.dist_dir}/{os.path.basename(rpm_artifact)}'
        artifacts = glob.glob(f'{rpms_dir}/**/{app_name}-{cov_to_safer_package_version(self.distribution.get_version())}-*.rpm')
        if not artifacts: return None

        shutil.copy(artifacts[0], self.dist_dir)
        return os.path.join(self.dist_dir, os.path.basename(artifacts[0]))

    def __make_common_archive(self, wheel_file:str) -> str:
        # Get archive file path 
        app_archive = os.path.join(self.dist_dir, "%s-%s.zip" % (
            cov_to_app_name(self.distribution.get_name()),
            cov_to_safer_package_version(self.distribution.get_version())
        ))

        # Make pip building directory
        # os.makedirs(self.pip_buiding_dir, exist_ok = True)

        # Make work directory
        work_dir = os.path.join(self.bdist_building_dir, 'zip')
        package_dir = os.path.join(work_dir, 'packages')
        os.makedirs(package_dir, exist_ok = True)

        # Make pip options
        pip_install_opts = ['--disable-pip-version-check']
        if self.pre: pip_install_opts.append('--pre')
        if self.binary: pip_install_opts.extend(['--only-binary', self.binary])

        # Save wheels into dists
        pip_wheel_opts = ["wheel", "-w", package_dir, wheel_file]
        if pip_install_opts: pip_wheel_opts.extend(pip_install_opts)
        if self.index_url: pip_wheel_opts.extend(f'--index-url={self.index_url}')
        if self.trusted_host: pip_wheel_opts.append(f'--trusted-host={self.trusted_host}')
        subprocess.call([sys.executable, "-m", "pip"] + pip_wheel_opts)

        #Scan app program
        app_program_set = set()
        for console_script in getattr(self.distribution, 'entry_points', {}).get('console_scripts', []):
            program_name, _, _ = re.split('\s?=\s?|\s?\:\s?', console_script)
            if not program_name.startswith(cov_to_app_name(self.distribution.get_name())): continue
            app_program_set.add(program_name)

        # Write installer
        with open(os.path.join(work_dir, 'install'), 'w', encoding='utf-8') as f:
            write_installer(
                f,
                cov_to_app_name(self.distribution.get_name()),
                os.path.basename(wheel_file),
                *list(app_program_set),
                pip_install_option = " ".join(pip_install_opts)
            )

        # Write license
        if not os.path.exists('LICENSE'):
            with open(os.path.join(work_dir, 'LICENSE'), 'w', encoding='utf-8') as f:
                f.write(self.distribution.get_license())
        else:
            shutil.copy('LICENSE', work_dir)

        # Write application distribution
        self.announce(f"Make archive: {app_archive}", level = log.INFO)
        with zipfile.ZipFile(app_archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for root_dir, _, file_names in os.walk(work_dir):
                for file_name in file_names:
                    file_path = os.path.join(root_dir, file_name)
                    file_arc_path = os.path.relpath(file_path, work_dir)
                    z.write(file_path, file_arc_path)
                    self.announce(f"Add '{file_path}' as '{file_arc_path}'", level = log.INFO)

        return app_archive        

    def run(self):
        ##########################################################################
        # 变了定义
        ##########################################################################

        dist_files = getattr(self.distribution, 'dist_files', [])

        ##########################################################################
        # 生成制品
        ##########################################################################
        # Find wheel distribution
        wheel_files = [ v for k, _, v in dist_files if 'bdist_wheel' == k ]
        wheel_file = wheel_files and wheel_files[0]
        if not wheel_file or not os.path.exists(wheel_file):
            raise Exception(f"Not found wheel")

        # Make common archive
        app_archive = self.__make_common_archive(wheel_file)
        dist_files.append(('bdist_artifact', get_python_version(), app_archive))

        # Make rpm artifact
        if self.rpm and ( artifact := self.__make_rpm_artifact(app_archive) ):
            dist_files.append(('bdist_artifact', get_python_version(), artifact))

        ##########################################################################
        # 生成报告
        ##########################################################################
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        report_file = os.path.join(self.dist_dir, f'artifact_{timestamp_str}.csv') 
        report_dir = os.path.dirname(report_file)
        os.makedirs(report_dir, exist_ok = True)

        dist_files.append(('bdist_artifact', get_python_version(), report_file))

        with open(report_file, mode = 'w', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["type", "file"])
            writer.writerows([(dist_type, dist_file) for dist_type, _, dist_file in dist_files])
        
        self.announce(f"Review: {report_file}", level = log.INFO)

        ##########################################################################
        # 插件处理
        ##########################################################################
        if self.plugin:
            for plugin_module in self.plugin.strip().split(":"):
                pm = plugin_module.strip()
                if not pm: continue
                try:
                    subprocess.run([sys.executable, "-m", pm, report_file])
                except ex:
                    self.warn(f"Run plugin failed: {str(ex)}")