class ProjectDefinition(object):
    def __init__(self, name, version, revision):
        self.name = name
        self.version = version
        self.revision = revision
        self.string_representation = self.name + " " + self.version + " " + self.revision

    def __repr__(self):
        return self.string_representation

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version and self.revision == other.revision
