# Streamlit Community Cloud Deployment

## Repository settings

Use the following deployment coordinates:

- Repository: the GitHub repository containing these extracted files
- Branch: `main`
- Main file path: `app.py`
- Python version: choose a currently supported version, preferably the same version used for local testing

## Deployment procedure

1. Extract the downloaded ZIP file.
2. Create a new empty GitHub repository.
3. Upload every extracted file and folder, not the ZIP itself.
4. Confirm that `app.py`, `requirements.txt`, and `README.md` appear at the repository root.
5. Open Streamlit Community Cloud and create an app from the repository.
6. Select branch `main` and enter `app.py` as the main file path.
7. Deploy.

## Updating the live app

Commit and push changes to the same GitHub branch. Streamlit Community Cloud will read the updated repository. Dependency changes should be made in `requirements.txt`.

## Troubleshooting

### `ModuleNotFoundError: No module named 'src'`

This repository's root `app.py` is self-contained and does not import a local `src` package. If this error appears, Streamlit is still deploying an older GitHub commit or a different entrypoint file. Confirm that the selected entrypoint is exactly `app.py`, then reboot or redeploy the app.

### Data file not found

The app resolves its sample CSV relative to the location of `app.py` and also contains built-in fallback examples. Keep `data/sample_user_history.csv` in the repository for the documented demo dataset.

### Dependency installation problem

Confirm that `requirements.txt` is at the repository root and contains one package requirement per line.
