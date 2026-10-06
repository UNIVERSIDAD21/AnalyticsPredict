"""El runner SQL solo acepta una base administradora local y desechable."""

import pytest

from scripts.run_suite_global_testdb import validar_admin_local


def test_runner_admite_postgres_local():
    validar_admin_local("postgresql://tester@127.0.0.1:5432/postgres?sslmode=disable")
    validar_admin_local("postgresql://tester@/postgres?host=/tmp/pg-test-sock")


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://tester@example.net:5432/postgres",
        "postgresql://tester@127.0.0.1:5432/analytics_prod",
    ],
)
def test_runner_rechaza_destinos_no_locales_o_no_administradores(url):
    with pytest.raises(ValueError, match="Solo se admite PostgreSQL local"):
        validar_admin_local(url)
