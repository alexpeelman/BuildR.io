
    ██████╗ ██╗   ██╗██╗██╗     ██████╗ ██████╗    ██╗ ██████╗
    ██╔══██╗██║   ██║██║██║     ██╔══██╗██╔══██╗   ██║██╔═══██╗
    ██████╔╝██║   ██║██║██║     ██║  ██║██████╔╝   ██║██║   ██║
    ██╔══██╗██║   ██║██║██║     ██║  ██║██╔══██╗   ██║██║   ██║
    ██████╔╝╚██████╔╝██║███████╗██████╔╝██║  ██║██╗██║╚██████╔╝
    ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝ ╚═════╝

# Table of Contents

1. [Overview](#overview)
2. [Running](#running)
3. [Behaviour](#behaviour)
4. [buildr.json](#buildr.json)
5. [Variables](#variables.json)
6. [TODO](#todo)
7. [Limitations](#limitations)
8. [Copyright and License](#copyright and License)

# Overview

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

# Running
## From source
```
$ python buildr/BuildR.py -d <folder containing buildr.json>
```
## Packaging and running on Mac OS X
```
$ ./package.sh
... 
Processing ./dist/buildr-0.0.1a1-py2.py3-none-any.whl
Installing collected packages: buildr
Successfully installed buildr-0.0.1a1 
```

```
$ buildr -d <folder containing buildr.json>
```   
   
# Behaviour

* BuildR tries to `resolve dependencies` from the given repositories. If this `fails` BuildR automatically falls back to building the dependency `from source` code.
* Build results are `not automatically uploaded` to the repositories, this must be requested explicitly by passing the `-p` or `--publish` option commandline. This is done to avoid accidental overrides.

For all possible options, please summon help

```
$ buildr -h
```


# buildr.json   

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
         "publish":"jfrog rt u \"**/*.rpm\" my_yum_repo --url {{ config.artifactory }} --props \"name={{ project.name }};version={{ project.version.result }};vcsRevision={{ project.revision.result }}\"",
         "resolve":"jfrog rt dl \"my-yum-repo/*.rpm\" --url {{ config.artifactory }} --props \"name={{ project.name }};version={{ project.version.result }};vcsRevision={{ project.revision.result }}\""
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
 
## Project

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
   
   
## Build
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
  
## Dependencies
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

## Repositories
```
{
  "repositories":[
      {
         "name":"my_yum_repo",
         "publish":"jfrog rt u \"**/*.rpm\" my_yum_repo --url {{ config.artifactory }} --props \"name={{ project.name }};version={{ project.version.result }};vcsRevision={{ project.revision.result }}\"",
         "resolve":"jfrog rt dl \"my-yum-repo/*.rpm\" --url {{ config.artifactory }} --props \"name={{ project.name }};version={{ project.version.result }};vcsRevision={{ project.revision.result }}\""
      }
   ]
}
```

The repositories property holds a list of repository configurations used for publishing and resolving artifacts from any kind of repository.
Required properties
 * publish, when a build is successful this command will be invoked. It should gather all binary results for a build and `upload` it to a repository in such a way
   that the binaries can be resolved `based on the data` found in the buildr.json file. 
 * resolve, when a dependency is handled BuildR first tries to fetch the binaries from the repositories by invoking this command. 

# Variables
## Environment variables
BuildR loads environment variables by default and they can be used directly in buildr.json definitions.
There is no need to specify any command line option to make use of this feature.

```
$ cat buildr.json
{
  "project": {
    "name": "Project {{ MY_ENV_VAR }}",
    "version": {
      "command": "echo '1.0.0_SNAPSHOT'"
    },
    "revision": {
      "command": "echo 'alpha'"
    }
    
    // ... skipped for brevity
}
```

```
$ export MY_ENV_VAR=magic-unicorns
```

```
$ buildr

INFO Running BuildR
INFO [command] echo '1.0.0_SNAPSHOT'
INFO [version] 1.0.0_SNAPSHOT
INFO [command] echo 'alpha'
INFO [revision] alpha
INFO [project] Project magic-unicorns 1.0.0_SNAPSHOT alpha
```

## Config file
A second option is to load variables from a JSON file via the `-c` or `--config` commandline parameter. 
The config file has higher precedence than environment variables and will override any previously defined environment variable.

```
$ cat config.json 
{
  "MY_ENV_VAR" : "fairies"
}
```

```
$ buildr -c config.json

INFO Running BuildR
INFO [command] echo '1.0.0_SNAPSHOT'
INFO [version] 1.0.0_SNAPSHOT
INFO [command] echo 'alpha'
INFO [revision] alpha
INFO [project] Project fairies 1.0.0_SNAPSHOT alpha
```

  
# TODO
   * Unit tests
 
# Limitations

This project is in POC and incubation phase.

# Copyright and License

Copyright 2016 Alex Peelman

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. 
