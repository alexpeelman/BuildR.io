import logging
from ProjectDefinition import ProjectDefinition


class Metadata(object):
    def __init__(self, project):
        self.__verify_project_definition__(project)
        self.project = project
        self.dependencies = []

    def __verify_project_definition__(self, project_definition):
        if not isinstance(project_definition, ProjectDefinition):
            raise ValueError("%s is not a project definition", project_definition)

    def add_dependency(self, project_definition):
        logging.debug("Adding dependency %s", project_definition)
        self.__verify_project_definition__(project_definition)
        self.dependencies.append(project_definition)

    def add_dependencies(self, dependencies):
        for dependency in dependencies:
            self.add_dependency(dependency)

    def get_dependencies_with_different_version(self, project_definition):
        self.__verify_project_definition__(project_definition)

        result = []
        for dependency in self.dependencies:
            if dependency.name == project_definition.name and dependency != project_definition:
                result.append(dependency)

        return result
