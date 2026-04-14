from iac.GitLabInfrastructureStack import GitLabInfrastructureStack


def main():
    GitLabInfrastructureStack().deploy()


if __name__ == "__main__":
    main()