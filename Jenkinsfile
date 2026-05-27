pipeline {
    agent any
    
    environment {
        // The address of the GRS Engine inside the docker network
        ENGINE_URL = 'http://grs-engine:8080'
        // The name of the built Docker image
        IMAGE_NAME = 'grs/app-candidate'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Image') {
            steps {
                script {
                    // Determine commit SHA
                    env.COMMIT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    echo "Building Docker image for version: ${env.COMMIT_SHA}"
                    
                    // Build the docker image
                    sh "docker build -t ${env.IMAGE_NAME}:${env.COMMIT_SHA} -f Dockerfile ."
                }
            }
        }
        
        stage('Deploy Trigger') {
            steps {
                script {
                    echo "Triggering deployment of version ${env.COMMIT_SHA} on GRS Engine..."
                    // Send a POST request to GRS Engine to perform the rollout
                    sh """
                        curl -X POST ${env.ENGINE_URL}/deploy \
                          -H "Content-Type: application/json" \
                          -d '{"image": "${env.IMAGE_NAME}", "version": "${env.COMMIT_SHA}"}'
                    """
                }
            }
        }
    }
}
