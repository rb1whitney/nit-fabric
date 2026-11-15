terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

resource "aws_lambda_function" "probe" {
  # checkov:skip=CKV_AWS_116: Synchronous diagnostic probe invoked on-demand via Function URL; no async event queue.
  function_name                  = "nit-fabric-probe"
  role                           = aws_iam_role.lambda_exec.arn
  handler                        = "aws_probe.lambda_handler"
  runtime                        = "python3.11"
  filename                       = var.lambda_zip_path
  reserved_concurrent_executions = 5
  tags                           = { "nit-fabric:type" = "probe" }

  tracing_config {
    mode = "Active"
  }

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}

resource "aws_lambda_function_url" "probe" {
  function_name      = aws_lambda_function.probe.function_name
  authorization_type = "AWS_IAM"
}

resource "aws_iam_role" "lambda_exec" {
  name = "nit_fabric_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_security_group" "lambda" {
  name        = "nit-fabric-lambda-sg"
  vpc_id      = var.vpc_id
  description = "Security group for nit-fabric AWS probe Lambda"

  egress {
    description = "Allow outbound HTTPS to allowed probe CIDRs"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_egress_cidrs
  }
}

variable "subnet_ids" { type = list(string) }
variable "vpc_id" { type = string }
variable "lambda_zip_path" { type = string }
variable "allowed_egress_cidrs" {
  type    = list(string)
  default = ["10.0.0.0/8"]
}

output "url" {
  value = aws_lambda_function_url.probe.function_url
}
