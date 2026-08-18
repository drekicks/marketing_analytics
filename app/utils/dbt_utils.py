import subprocess
from app.config.paths import DBT_PROJECT_DIR


def run_dbt_build():
    result = subprocess.run(
        ["dbt", "build"],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("dbt build failed.")

    print(result.stdout)

    return result

run_dbt_build()