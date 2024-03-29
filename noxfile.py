import nox


@nox.session(
    python=["3.8", "3.9", "3.10"],
    reuse_venv=True,
)
def tests(session: nox.Session):
    session.install("-e", ".", "pytest")
    session.run("pytest")
