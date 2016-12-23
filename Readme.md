# BuildR

#### Table of Contents

1. [Overview](#overview)
2. [buildr.json](#buildr.json)
3. [TODO](#todo)
4. [Limitations](#limitations)
5. [Copyright and License](#license)

## Overview

BuildR aims to be an environment agnostic and zero opinionated recursive build tool.
It focuses on the general steps performed when building stuff not on the how. 

A build 
* Always starts from `source`. It is, no pun intended, the source of truth.
All metadata and information captured to link build results must be derived from it.
* Has a `recipe` and preferably an `isolated build environment` to execute this recipe.  
* Generates a `result` which must be uploaded to a repository and linked to the source it originated from. 
Extra points go to repositories that can be queried to retrieve binaries based on source information. This avoids an unnecessary step of rebuilding stuff already present in the repository.
* Has 0 or more `dependencies` which make up the `build tree`. 
This build tree will be traversed depth first, meaning that leave nodes are build or resolved first 
assuring that all dependencies are available when running the build.

   
## buildr.json   

BuildR starts from a very simple template `buildr.json` that expects 
   * A project definition
   * Repositories for resolving and publishing binary build results
   * Dependencies 
   * A build recipe 
   * Variables 

An example
```
{
   "project":{
      "name":"my-project",
      "version":{
         "command":"echo '1.0.0-SNAPSHOT'"
      },
      "revision":{
         "command":"git log -n 1 | grep commit | cut -d' ' -f2"
      }
   },
   "build":{
      "docker":{
         "folder":"tmp",
         "image":"my-docker-image:1.7"
      },
      "dependencies":{
         "folder":"/tmp/dependencies"
      },
      "command":"docker run -v $(pwd):/{{ build.docker.folder }} {{ config.docker.registry }}/{{ build.docker.image }} cd /{{ build.docker.folder }} && mvn clean install -DskipTests"
   },
   "dependencies":[
      {
         "folder":"{{ build.dependencies.folder }}/build-stuff",
         "resolve":"git clone --depth 1 --branch {{ versioning.build_stuff | default('master') }} {{ config.git.server }}/REPO/build-stuff.git {{ build.dependencies.folder }}/build-stuff"
      }
   ],
   "repositories":[
      {
         "name":"my_yum_repo",
         "publish":"jfrog rt u **/*.rpm {{ config.artifactory }} my_yum_repo --props name={{ project.name }};version={{ project.version.result }};vcsRevision={{ project.revision.result }}",
         "resolve":"jfrog rt dl *.rpm --props \"name={{ project.name }};version={{ project.version.result }};vcsRevision={{ project.revision.result }}\" {{ config.artifactory }} my_yum_repo {{ build.dependencies.folder }}"
      }
   ],
   "config":{
      "git":{
         "server":"ssh://pea@git.newtec.eu/git"
      },
      "docker":{
         "registry":"artifactory.newtec.eu:10001/ntc-docker"
      },
      "artifactory":"http://artifactory.newtec.eu/artifactory"
   }
}
    
```

Lets describe each part of the definition file in depth.
 
### project

```
{
  "project":{
    "name":"my-project",
    "version":{
       "command":"echo '1.0.0-SNAPSHOT'"
    },
    "revision":{
       "command":"git log -n 1 | grep commit | cut -d' ' -f2"
    }
 }
}
```

The project property describes the metadata related to the source code. Required properties are 
 * name
 * version.command, which is `executed` to retrieve the version of the source code
   The output of the command is placed in the `project.version.result` variable and can be used in the template.
 * revision.command, which is `executed` to retrieve the revision of the source code.
   The output of the command is placed in the `project.revision.result` variable and can be used in the template.
   In this particular case the git commit hash is extracted via a bash command.
   
   
### build
```
{
  "build":{
    "docker":{
       "folder":"tmp",
       "image":"my-docker-image:1.7"
    },
    "dependencies":{
       "folder":"/tmp/dependencies"
    },
    "command":"docker run -v $(pwd):/{{ build.docker.folder }} {{ config.docker.registry }}/{{ build.docker.image }} cd /{{ build.docker.folder }} && mvn clean install -DskipTests"
  }
}
```

The build property has only one required property
  * command, which is `executed` to build the source code. This can be a one liner, BASH script, a make command, ...
  
### dependencies
```  
{
  "dependencies":[
    {
       "folder":"{{ build.dependencies.folder }}/build-stuff",
       "resolve":"git clone --depth 1 --branch {{ versioning.build_stuff | default('master') }} {{ config.git.server }}/REPO/build-stuff.git {{ build.dependencies.folder }}/build-stuff"
    }
  ],
}
```

The dependencies property holds a list of dependency configurations. Each dependency is handled before invoking the actual build command in the buildr.json file. 
Required properties for a dependency entry are
  * folder, used to verify if a dependency has been resolved by checking the existence (not the content) of the folder
  * resolve, a command used to fetch the dependency. Please do pay attention that the resolved result must end up in the same folder described in the previous bullet point. 

### repositories
```
{
  "repositories":[
      {
         "name":"my_yum_repo",
         "publish":"jfrog rt u **/*.rpm {{ config.artifactory }} my_yum_repo --props name={{ project.name }};version={{ project.version.result }};vcsRevision={{ project.revision.result }}",
         "resolve":"jfrog rt dl *.rpm --props \"name={{ project.name }};version={{ project.version.result }};vcsRevision={{ project.revision.result }}\" {{ config.artifactory }} my_yum_repo {{ build.dependencies.folder }}"
      }
   ]
}
```

The repositories property holds a list of repository configurations used for publishing and resolving artifacts from any kind of repository.
Required properties
 * publish, when a build is successful this command will be invoked. It should gather all binary results for a build and `upload` it to a repository in such a way
   that the binaries can be resolved `based on the data` found in the buildr.json file. 
 * resolve, when a dependency is handled BuildR first tries to fetch the binaries from the repositories by invoking this command. 

  
## TODO
   * Use and expose environment variables
 
## Limitations

This project is in POC and incubation phase.

## Copyright and License

Copyright (C) 2016 Alex Peelman

License still under debate 
