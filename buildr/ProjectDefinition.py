class ProjectDefinition(object):
    def __init__(self, name, version, revision):
        self.name = name
        self.version = version
        self.revision = revision
        self.fullName = self.name + " " + self.version + " " + self.revision

    def __repr__(self):
        return self.fullName

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version and self.revision == other.revision
