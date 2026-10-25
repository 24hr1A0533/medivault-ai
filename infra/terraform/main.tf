terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "MediVault-HOS"
      Environment = "Production"
      HIPAA       = "Compliant"
      ManagedBy   = "Terraform"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# 1. HIPAA-Compliant Multi-AZ VPC Architecture
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "medivault_vpc" {
  cidr_block           = "10.100.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "medivault-production-vpc"
  }
}

# 3 Private Subnets across 3 Availability Zones
resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.medivault_vpc.id
  cidr_block        = "10.100.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name                              = "medivault-private-az-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# 3 Public Subnets for Ingress Load Balancers
resource "aws_subnet" "public" {
  count                   = 3
  vpc_id                  = aws_vpc.medivault_vpc.id
  cidr_block              = "10.100.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                     = "medivault-public-az-${count.index + 1}"
    "kubernetes.io/role/elb" = "1"
  }
}

# Internet Gateway & NAT Gateways
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.medivault_vpc.id
  tags = {
    Name = "medivault-igw"
  }
}

# 2. IAM Role for EKS Control Plane
resource "aws_iam_role" "medivault_eks_role" {
  name = "medivault-production-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.medivault_eks_role.name
}

resource "aws_iam_role_policy_attachment" "eks_service_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  role       = aws_iam_role.medivault_eks_role.name
}

# 3. KMS Master Key for PHI Encryption
resource "aws_kms_key" "medivault_master_key" {
  description             = "MediVault AI HIPAA Master Encryption Key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "medivault-phi-master-key"
  }
}

resource "aws_kms_alias" "medivault_master_key_alias" {
  name          = "alias/medivault-phi-master-key"
  target_key_id = aws_kms_key.medivault_master_key.key_id
}

# 4. HIPAA Multi-AZ EKS Cluster
resource "aws_eks_cluster" "medivault_cluster" {
  name     = "medivault-production-eks"
  role_arn = aws_iam_role.medivault_eks_role.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = aws_subnet.private[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.medivault_master_key.arn
    }
    resources = ["secrets"]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_service_policy
  ]
}

# Outputs for CD pipelines
output "eks_cluster_endpoint" {
  value = aws_eks_cluster.medivault_cluster.endpoint
}

output "eks_cluster_name" {
  value = aws_eks_cluster.medivault_cluster.name
}

output "vpc_id" {
  value = aws_vpc.medivault_vpc.id
}
