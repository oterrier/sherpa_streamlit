pipeline {

  environment {
    PATH_HOME = "/home/jenkins"
    PYTHONDONTWRITEBYTECODE = "1"
    PYTHONPYCACHEPREFIX = "/tmp/.pytest_cache"
    TEST_REPORT_DIR="/root/test-reports"
    MAJOR_VERSION = "0"
    MINOR_VERSION = "1"
    GIT_AUTH = credentials('bitbucket-user')
  }

  agent none

  triggers {
    upstream(upstreamProjects: "pymultirole_plugins/" + env.BRANCH_NAME.replaceAll("/", "%2F"),\
                                threshold: hudson.model.Result.SUCCESS)
  }

  parameters {
      booleanParam(defaultValue: false, description: 'if set to true (ticked), it will not skip on CI commit', name: 'forcePublishing')
  }

  stages {

    stage('Generate new version') {
      agent {
        node {
          label 'master'
          customWorkspace "/home/jenkins/${env.JOB_NAME}"
        }
      }

      stages {

        stage('Add credentials') {
          steps {
            script {
              // Add password file for flit publishing
              sh "cp ${env.PATH_HOME}/.passwd-pypi .env"
            }
          }
        }

        stage('Skip on CI commit') {
          steps {
            script {
              // returnStatus = 1 when string not found -> Team commit
              // returnStatus = 0 when string is found  -> CI commit
              env.LAST_COMMIT_IS_TEAM = sh(
                      script: 'git log -1 | grep "\\[Jenkins CI\\]"',
                      returnStatus: true
              )
              if (LAST_COMMIT_IS_TEAM == '0') {
                println "Last commit has been done by CI, skipping next steps"
              } else {
                println "Last commit has been done by Team, processing"
              }
              if (params.forcePublishing) {
                println "Try to publish, considering last commit has been done by Team"
                env.LAST_COMMIT_IS_TEAM = "1"
              }
            }
          }
        }

        stage('Commit new version') {
          when {
            environment name: "LAST_COMMIT_IS_TEAM", value: "1"
          }
          steps {
            script {
              println("attempt to publish ${env.JOB_NAME} with version: ${MAJOR_VERSION}.${MINOR_VERSION}.${env.BUILD_ID}")

              // push updates of file __init__.py
              sh "echo '\"\"\"Generate a focussed segments view of an annotated corpus\"\"\"' > src/sherpa_streamlit/__init__.py"
              sh "echo '__version__ = \"${MAJOR_VERSION}.${MINOR_VERSION}.${env.BUILD_ID}\"' >> src/sherpa_streamlit/__init__.py"
              sh('''
                git config --remove-section credential >/dev/null 2>&1 || true
                git config --remove-section user >/dev/null 2>&1 || true
                git config --global push.default matching
                git config user.name 'Guillaume Karcher'
                git config user.email 'guillaume.karcher@kairntech.com'
                git commit src/sherpa_streamlit/__init__.py -m "[Jenkins CI] Commit on version files" || echo "No changes to commit"
                git config --local credential.helper "!f() { echo username=\\$GIT_AUTH_USR; echo password=\\$GIT_AUTH_PSW; }; f"
                git push
                git config --remove-section credential
                git config --remove-section user
              ''')
            }
          }
        }

      }
    }

    stage('Build, test and publish') {
      when {
        environment name: "LAST_COMMIT_IS_TEAM", value: "1"
      }

      agent {
        // dockerfile agent
        // Mounted volume for Junit reports
        //   - docker: /root/test-reports
        //   - host  : /tmp/_${env.JOB_NAME}/test-reports
        dockerfile {
          label 'master'
          customWorkspace "/home/jenkins/${env.JOB_NAME}"
          filename 'Dockerfile'
          args "-u root --privileged -v /tmp/_${env.JOB_NAME}/test-reports:${TEST_REPORT_DIR}"
        }
      }

      stages {

        stage('Install flit & flake8') {
          steps {
            // remove any previous tox env
            sh 'rm -rf .tox'
            sh 'pip install --no-cache-dir flit==3.2.0 flake8==3.9.0 flakehell tox'
            sh 'flit install'
          }
        }

        stage('Test & lint python code') {
          steps {
            sh 'tox'
          }
        }

        stage('Publish on PyPI') {
          environment {
            FLIT_USERNAME = getUserName ".env"
            FLIT_PASSWORD = getUserPass ".env"
          }
          steps {
            // remove any previous folder dist
            sh 'rm -rf dist'
            // create (as root) folder dist
            sh 'mkdir dist'
            // pull recent updates of file __init__.py
            sh('''
              git config --remove-section credential >/dev/null 2>&1 || true
              git config --remove-section user >/dev/null 2>&1 || true
              git config --global pull.rebase false
              git config user.name 'Guillaume Karcher'
              git config user.email 'guillaume.karcher@kairntech.com'
              git config --local credential.helper "!f() { echo username=\\$GIT_AUTH_USR; echo password=\\$GIT_AUTH_PSW; }; f"
              git pull
              git config --remove-section credential
              git config --remove-section user
            ''')
            // put back owner of pulled file
            sh 'chown 1000:1000 src/sherpa_streamlit/__init__.py'
            // publish on PyPI
            sh 'git status'
            sh 'flit publish'
            // remove current folder dist
            sh 'rm -rf dist'
          }
        }

      }

    }

  }

  post {
    // only triggered when blue or green sign
    //success {
    //}
    // triggered when red sign
    //failure {
    //}
    // trigger every-works
    always {
      // node is specified here to get an agent
      node('master') {
        // keep using customWorkspace to store Junit report
        ws("/home/jenkins/${env.JOB_NAME}") {
          script {
            try {
              sh(
                script: "ln -s /tmp/_${env.JOB_NAME}/test-reports/results.xml $WORKSPACE",
                returnStatus: true
              )
              junit 'results.xml'
            } catch (Exception e) {
              echo 'Exception occurred: ' + e.toString()
            }
            println "sending Systematic Build notification"
            emailext(body: '${DEFAULT_CONTENT}', mimeType: 'text/html',
                    replyTo: '${DEFAULT_REPLYTO}', subject: '${DEFAULT_SUBJECT}',
                    to: '${DEFAULT_RECIPIENTS}')
          }
        }
      }
    }
  }

}

// return FLIT_USERNAME from given file
def getUserName(path) {
  USERNAME = sh(
                 script: "grep FLIT_USERNAME ${path}|cut -d '=' -f2",
                 returnStdout: true
               ).trim()
  return USERNAME
}

// return FLIT_PASSWORD from given file
def getUserPass(path) {
  USERPASS = sh(
                 script: "grep FLIT_PASSWORD ${path}|cut -d '=' -f2",
                 returnStdout: true
               ).trim()
  return USERPASS
}
