from lagrangelog import *
import lagrange
import enum
import tarfile


class ExperimentFilesMissing(Exception):
    pass


class TrialDirectory:
    def __init__(self, path):
        self._path = os.path.abspath(path)
        self.findFiles()

    def findFiles(self):
        for filename in self._get_files():
            filename = os.path.abspath(filename)
            filetype = self._classify_file(filename)
            if filetype == LagrangeLogFileType.Misc:
                continue
            if filetype == LagrangeLogFileType.Unknown:
                continue

            if filetype == LagrangeLogFileType.BGKey:
                self._bgkey_filename = filename
            if filetype == LagrangeLogFileType.BGStates:
                self._bgstates_filename = filename
            if filetype == LagrangeLogFileType.ResultsJSON:
                self._json_filename = filename
            if filetype == LagrangeLogFileType.ConsoleLog:
                self._console_filename = filename

            if filetype == LagrangeLogFileType.Config:
                self._config_filename = filename
            if filetype == LagrangeLogFileType.Phylip:
                self._align_filename = filename
            if filetype == LagrangeLogFileType.Newick:
                self._tree_filename = filename

    @staticmethod
    def _classify_file(filename):
        basename, extension = os.path.splitext(filename)
        if extension == '.log':
            return LagrangeLogFileType.ConsoleLog
        if extension == '.tre':
            subbasename, subextension = os.path.splitext(basename)
            if subextension == '.bgkey':
                return LagrangeLogFileType.BGKey
            if subextension == '.bgstates':
                return LagrangeLogFileType.BGStates
        if extension == '.nwk':
            return LagrangeLogFileType.Newick
        if extension == '.phy':
            return LagrangeLogFileType.Phylip
        if extension == '.conf':
            return LagrangeLogFileType.Config
        if extension == '.json':
            return LagrangeLogFileType.ResultsJSON
        return LagrangeLogFileType.Unknown

    def _get_files(self):
        return [
            os.path.join(self._path, f) for f in os.listdir(self._path)
            if os.path.isfile(os.path.join(self._path, f))
        ]

    def convertToExpectedDirectory(self):
        new_path = os.path.join(self._path, "expected")
        os.mkdir(new_path)
        if hasattr(self, '_json_filename'):
            shutil.move(self._json_filename, new_path)
        shutil.move(self._console_filename, new_path)
        return ExpectedTrialDirectory(new_path)

    def convertToExperimentDirectory(self):
        new_path = os.path.join(self._path, "experiment")
        os.mkdir(new_path)
        shutil.move(self._config_filename, new_path)
        shutil.move(self._align_filename, new_path)
        shutil.move(self._tree_filename, new_path)
        return ExperimentTrialDirectory(new_path)

    def convert(self):
        expected_dir = self.convertToExpectedDirectory()
        experiment_dir = self.convertToExperimentDirectory()
        for f in self._get_files():
            os.remove(f)
        return (expected_dir, experiment_dir)

    def _registerLog(self):
        if hasattr(self, '_json_filename'):
            self._lagrange_log = LagrangeLog(self._console_filename,
                                             self._json_filename)
        else:
            self._lagrange_log = LagrangeLog(self._console_filename)

    def binaryCompare(self, other):
        return self._lagrange_log == other._lagrange_log

    def metricCompare(self, other):
        return self._lagrange_log.wassersteinMetric(other._lagrange_log)

    def parameterVectorDifference(self, other):
        return numpy.abs(self._lagrange_log.paramsVector() -
                         other._lagrange_log.paramsVector())

    def __repr__(self):
        sub_path, basename = os.path.split(self._path)
        if basename == 'experiment' or basename == 'expected':
            return sub_path
        return self._path


class ExpectedTrialDirectory(TrialDirectory):
    def __init__(self, path):
        super(ExpectedTrialDirectory, self).__init__(path)
        self._registerLog()


class ExperimentTrialDirectory(TrialDirectory):
    def __init__(self, path):
        super(ExperimentTrialDirectory, self).__init__(path)

    def runExperiment(self, lagrange_runner):
        lagrange_runner.run(self._path, self._config_filename)
        self.findFiles()
        try:
            self._registerLog()
        except ExperimentFilesMissing:
            self._failed = True
            raise ExperimentFilesMissing
        self._failed = False

    def failed(self):
        return self._failed

    def setFailed(self):
        self._failed = True


class ExperimentWithDistance:
    def __init__(self, exp, dist):
        self._exp = exp
        self._dist = dist

    def __repr__(self):
        return "(%s, %f)" % (self._exp, self._dist)


def DirectoryRepresenter(dumper, data):
    return dumper.represent_scalar(u'!FailedError', u'%s' % data._path)


def ExperimentWithDistanceRepresenter(dumper, data):
    return dumper.represent_scalar(u'!FailedDistance',
                                   u'(%s, %f)' % (data._exp._path, data._dist))


def isExperimentDirectory(files):
    for f in files:
        basename, ext = os.path.splitext(f)
        if ext == ".conf":
            return True
    return False


def extractTarFileAndMakeDirectories(tarfile_path, destination_path, progress):
    extract_task = progress.add_task("[red]Extracting...", total=1.0)

    tar = tarfile.open(tarfile_path)
    tar.extractall(path=destination_path)

    directories = []
    for root, dirs, files in os.walk(destination_path):
        if isExperimentDirectory(files):
            directories.append(TrialDirectory(root))

    progress.update(extract_task, advance=1.0)

    convert_task = progress.add_task("[red]Converting...",
                                     total=len(directories))

    converted_directories = []
    for d in directories:
        converted_directories.append(d.convert())
        progress.update(convert_task, advance=1.0)

    progress.update(extract_task, visible=False)
    progress.update(convert_task, visible=False)
    return converted_directories
