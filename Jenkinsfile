// CI/CD pipeline: test -> SonarQube -> build -> Trivy scan -> push to ECR -> bump Helm tag (ArgoCD deploys)
pipeline {
    agent { label 'docker' }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        AWS_REGION   = 'ap-south-1'
        ECR_REGISTRY = '123456789012.dkr.ecr.ap-south-1.amazonaws.com'
        IMAGE_TAG    = "${env.GIT_COMMIT.take(7)}"
        SERVICES     = 'product-service order-service'
    }

    stages {
        stage('Unit tests') {
            parallel {
                stage('product-service') {
                    steps { sh 'bash scripts/run-tests.sh product-service' }
                }
                stage('order-service') {
                    steps { sh 'bash scripts/run-tests.sh order-service' }
                }
            }
            post {
                always { junit 'services/*/test-results.xml' }
            }
        }

        stage('SonarQube analysis') {
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh 'sonar-scanner -Dsonar.projectVersion=${IMAGE_TAG}'
                }
            }
        }

        stage('Quality gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build images') {
            steps {
                script {
                    env.SERVICES.split().each { svc ->
                        sh "docker build -t ${ECR_REGISTRY}/${svc}:${IMAGE_TAG} services/${svc}"
                    }
                }
            }
        }

        stage('Trivy image scan') {
            steps {
                script {
                    env.SERVICES.split().each { svc ->
                        sh """
                          trivy image --no-progress --ignore-unfixed \
                            --severity HIGH,CRITICAL --exit-code 1 \
                            ${ECR_REGISTRY}/${svc}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('Push to ECR') {
            when { branch 'main' }
            steps {
                withAWS(credentials: 'aws-jenkins', region: "${AWS_REGION}") {
                    sh 'aws ecr get-login-password | docker login --username AWS --password-stdin ${ECR_REGISTRY}'
                    script {
                        env.SERVICES.split().each { svc ->
                            sh "docker push ${ECR_REGISTRY}/${svc}:${IMAGE_TAG}"
                        }
                    }
                }
            }
        }

        stage('Update Helm values (GitOps)') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-bot', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                    sh 'bash scripts/bump-image-tag.sh ${IMAGE_TAG}'
                }
            }
        }
    }

    post {
        success {
            slackSend(channel: '#deployments', color: 'good',
                message: "Released ${env.JOB_NAME} ${IMAGE_TAG}. ArgoCD will roll it out to EKS.")
        }
        failure {
            slackSend(channel: '#deployments', color: 'danger',
                message: "Pipeline failed: ${env.JOB_NAME} #${env.BUILD_NUMBER} (${env.BUILD_URL})")
        }
        always { sh 'docker image prune -f || true' }
    }
}
