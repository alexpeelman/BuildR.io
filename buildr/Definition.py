import os
import json
import logging
import Util
from Metadata import Metadata
from ProjectDefinition import ProjectDefinition
from jinja2 import Environment, FileSystemLoader, Template, StrictUndefined, UndefinedError


class Definition(object):
    FILE_NAME = "buildr.json"
    METADATA_FILE_NAME = "buildr.metadata.json"

    # BUILDR DEFAULT PROPERTIES
    BUILDR_NAMESPACE = "_buildr"
    BUILDR_FILE = "file"

    # PROPERTIES
    BUILD = "build"
    COMMAND = "command"
    PROJECT = "project"
    NAME = "name"
    VERSION = "version"
    REPOSITORIES = "repositories"
    RESOLVE = "resolve"
    PUBLISH = "publish"
    REVISION = "revision"
    RESULT = "result"
    DEPENDENCIES = "dependencies"
    FOLDER = "folder"
    DEFINITION = "definition"

    def __init__(self, options, path=os.getcwd()):
        os.chdir(path)
        logging.info("[cwd] %s", os.getcwd())

        self.options = options
        self.project_definition = None
        self.metadata = None
        self.path = os.getcwd()
        self.__resolve_variables__()
        self.metadata = Metadata(self.get_project_definition())
        self.__verify_project_versioning__()

    def __resolve_variables__(self, skip_version=False, skip_revision=False):
        self.properties = self.__read_file__(Definition.FILE_NAME)
        self.config = self.__read_config_file__()
        self.__add_default_properties__()
        self.__version__()
        self.__revision__()
        self.__generateProperties__()

    def __read_file__(self, path):
        logging.debug("[load definition] %s", path)

        try:
            with open(path) as data_file:
                return json.load(data_file)
        except ValueError as e:
            logging.error("[error] Invalid JSON %s/%s : %s. There is probably a syntax error in your definition", self.path, path,
                          e.message)
            raise e
        except IOError as e:
            logging.error("[error] Problem while loading %s : %s", path, e.strerror)
            raise e

    def __read_config_file__(self):
        if self.options.config_file():
            return self.__read_file__(self.options.config_file())

        return {}

    def __add_default_properties__(self):
        self.properties[Definition.BUILDR_NAMESPACE] = {}
        self.properties[Definition.BUILDR_NAMESPACE][Definition.BUILDR_FILE] = Definition.FILE_NAME
        self.properties[Definition.BUILDR_NAMESPACE][Definition.DEPENDENCIES] = []

        if self.metadata:
            self.properties[Definition.BUILDR_NAMESPACE][Definition.DEPENDENCIES] = self.metadata.dependencies

    def __generateProperties__(self):
        logging.debug("[properties] Resolving variables")

        try:
            env = Environment(loader=FileSystemLoader(self.path), undefined=StrictUndefined)
            template = env.get_template(Definition.FILE_NAME)
            merged_properties = Util.merge_dicts_and_copy(os.environ, self.config, self.properties)
            rendered_template = template.render(merged_properties)
        except UndefinedError as e:
            logging.error("Failed to resolve variable : %s. Please verify if your definition contains the right variables.",
                          e.message)
            raise e

        number_of_variables = rendered_template.count("{{")
        new_properties = json.loads(rendered_template)
        self.properties = Util.merge_dicts(self.properties, new_properties)

        while number_of_variables > 0:
            logging.debug("[properties] Resolving another %d variables", number_of_variables)

            try:
                # keep resolving until all variables are gone
                properties_as_json = json.dumps(self.properties)
                merged_properties = Util.merge_dicts_and_copy(self.properties, self.config, os.environ)
                rendered_template = Template(properties_as_json).render(merged_properties)
                left_over_number_of_variables = rendered_template.count("{{")

                if left_over_number_of_variables >= number_of_variables:
                    raise ValueError(
                        "Unable to resolve all properties, please check your %s file: %s" % (Definition.FILE_NAME, rendered_template)
                    )

                number_of_variables = left_over_number_of_variables
                self.properties = json.loads(rendered_template)
            except ValueError as e:
                logging.error("Failed to parse JSON %s from template content\n %s", e, rendered_template)

        logging.debug("[properties] %s", self.properties)

    def __verify_project_versioning__(self):
        other_versions = self.metadata.get_dependencies_with_different_version(self.get_project_definition())

        if not self.options.skip_dependency_checking() and other_versions:
            logging.error("[version mismatch] The same project with another version has been encountered %s", other_versions)
            raise ValueError("Version mismatch encountered for %s, other versions %s. Please verify build dependencies.",
                             self.get_project_definition(),
                             other_versions)

    def __version__(self):
        version = Util.run_command(
            self.properties[Definition.PROJECT][Definition.VERSION][Definition.COMMAND],
        )

        self.properties[Definition.PROJECT][Definition.VERSION][Definition.RESULT] = version
        logging.info("[version] %s", version)

    def __revision__(self):
        revision = Util.run_command(
            self.properties[Definition.PROJECT][Definition.REVISION][Definition.COMMAND],
        )

        self.properties[Definition.PROJECT][Definition.REVISION][Definition.RESULT] = revision
        logging.info("[revision] %s", revision)

    def __resolve_or_build__(self):
        # scoping in python :rolleyes:
        SOURCE_BUILD_REQUESTED = "source_build_requested"

        options = {
            SOURCE_BUILD_REQUESTED: self.options.source_build() or not self.properties[Definition.REPOSITORIES]
        }

        if not options[SOURCE_BUILD_REQUESTED]:
            for repository in self.properties[Definition.REPOSITORIES]:
                logging.info("[resolve] %s", repository[Definition.NAME])
                command = repository[Definition.RESOLVE]
                try:
                    Util.run_command(command)
                except ValueError as e:
                    logging.error("[resolve] error while resolving %s via %s : %s", self.get_project_definition(), command, e)
                    if self.options.binary_build():
                        logging.debug("[resolve] binary build explicitly requested, aborting build %s", self.get_project_definition())
                        raise e
                    else:
                        logging.debug("[resolve] forcing source build of %s", self.get_project_definition())
                        options[SOURCE_BUILD_REQUESTED] = True

        if options[SOURCE_BUILD_REQUESTED]:
            self.__build__()
            self.__publish__()

    def __build__(self):
        self.__handle_dependencies__()

        if not self.options.skip_build():
            try:
                logging.info("[build] %s", self.get_project_definition())
                Util.run_command(self.properties[Definition.BUILD][Definition.COMMAND])
            except Exception as e:
                logging.error("[error] build failed %s", e)
                raise e
        else:
            logging.info("[build] skip build of %s", self.get_project_definition())

    def __publish__(self):
        if self.options.skip_build or not self.options.publish:
            logging.info("[publish] skip publishing of %s", self.get_project_definition())
            return

        if not self.properties[Definition.REPOSITORIES]:
            logging.info("[publish] skip publishing of %s, no repositories defined", self.get_project_definition())

        for repository in self.properties[Definition.REPOSITORIES]:
            logging.info("[publish] %s %s", self.get_project_definition(), repository[Definition.NAME])
            command = repository[Definition.PUBLISH]
            try:
                Util.run_command(command)
            except Exception as e:
                logging.info("[error] failed to publish %s : %s", self.get_project_definition(), e)
                raise e

    def __handle_dependencies__(self):
        if not self.properties.has_key(Definition.DEPENDENCIES) or not self.properties[Definition.DEPENDENCIES]:
            logging.info("[dependency management] %s has no dependencies", self.get_project_definition())
            return

        logging.info("[dependency management] %s", self.get_project_definition())
        for dependency in self.properties[Definition.DEPENDENCIES]:
            self.__handle_dependency__(dependency)

        logging.info("[dependency management] reloading variables in %s after dependency changes", self.get_project_definition())
        self.__resolve_variables__()

    def __handle_dependency__(self, dependency):
        cwd = os.getcwd()

        try:
            self.__resolve_dependency__(dependency)
            self.__build_dependency__(dependency)
        finally:
            os.chdir(cwd)

    def __resolve_dependency__(self, dependency):
        folder = dependency[Definition.FOLDER]
        command = dependency[Definition.RESOLVE]

        try:
            logging.info("[verify] %s", folder)

            if os.path.isdir(folder) and os.listdir(folder):
                logging.info("[exists] %s", folder)
            else:
                logging.info("[resolve] %s", folder)
                self.__read_definition__(folder, dependency)
                if not self.options.skip_source_resolving():
                    Util.run_command(command)

        except Exception as e:
            logging.error("[error %s] could not resolve %s %s", self.get_project_definition(), command, e)
            raise e

    def __build_dependency__(self, dependency):
        folder = dependency[Definition.FOLDER]
        buildr = dependency[Definition.FOLDER] + "/" + Definition.FILE_NAME

        logging.info("[verify] %s", buildr)

        if os.path.isfile(buildr):
            logging.info("[build node] %s", buildr)
            definition = Definition(self.options, path=folder)
            definition.build()
            self.metadata.add_dependencies(definition.metadata.dependencies)
            self.metadata.add_dependency(definition.get_project_definition())
        else:
            logging.warning("[leaf node] %s contains no %s", folder, Definition.FILE_NAME)

    """
    Read the BuildR definition before actually resolving source code
    """

    def __read_definition__(self, folder, dependency):
        logging.debug("[resolve] copying %s in %s", Definition.FILE_NAME, folder)
        command = dependency[Definition.DEFINITION]

        try:
            buildr_definition = Util.run_command(command)

            if not os.path.exists(folder):
                os.makedirs(folder)

            with open(folder + "/" + Definition.FILE_NAME, "w") as buildr_file:
                buildr_file.write(json.dumps(json.loads(buildr_definition), indent=4))

        except Exception as e:
            logging.error("[error %s] Unable to fetch %s via %s : %s", self.get_project_definition(), Definition.FILE_NAME, command, e)

    def __generate_metadata__(self):
        try:
            with open(Definition.METADATA_FILE_NAME, 'w') as file:
                json.dump(self.metadata, file, default=Util.to_json, indent=4, sort_keys=True)
                logging.info("[metadata] the metadata of %s can be found in %s/%s", self.get_project_definition(), os.getcwd(), Definition.METADATA_FILE_NAME)
        except Exception as e:
            logging.error("[error %s] Unable to write metadata : %s", self.get_project_definition(), e)

    def get_project_definition(self):
        if not self.project_definition:
            self.project_definition = ProjectDefinition(
                self.properties[Definition.PROJECT][Definition.NAME],
                self.properties[Definition.PROJECT][Definition.VERSION][Definition.RESULT],
                self.properties[Definition.PROJECT][Definition.REVISION][Definition.RESULT],
            )

        return self.project_definition

    def build(self):
        logging.info("[project] %s", self.get_project_definition())
        self.__resolve_or_build__()
        self.__generate_metadata__()
        return self

    def properties(self):
        return self.properties
