# OpenET 2

OpenET 2 is a modular Python toolkit for collecting, organising, validating,
benchmarking, visualising, and comparing remote eye-tracking data over time.
It extends the supplied OpenET framework with a repeatable research workflow
while keeping source recordings read-only.

The system is designed for researchers who need consistent session metadata,
multi-format import, automated quality checks, reproducible metrics, static HTML
reports, and repeated-measurement comparisons across devices and study visits.

## Project capabilities

OpenET 2 implements the ten capabilities defined in the project brief:

1. A maintainable extension of the existing OpenET framework.
2. Structured session folders and session identifiers.
3. A repeatable calibration, validation, recording, and completion workflow.
4. Device, participant, display, calibration, and environment metadata.
5. Extensible CSV, TSV, and JSON import.
6. Automated checks for missing, invalid, duplicated, irregular, or incomplete data.
7. Sampling, completeness, precision, stability, calibration, and repeatability metrics.
8. Recording-level and cohort-level visualisations in portable HTML reports.
9. Long-term and participant-matched comparison across repeated sessions.
10. Installation, user, developer, example, and technical documentation.

Implementation and verification links are listed in
`docs/requirements_traceability.md`.

## Repository layout

```text
.
|-- src/openet2/       Runtime package
|-- tests/             Unit, integration, and requirement tests
|-- docs/              User, developer, research, and technical documentation
|-- examples/          Safe example inputs and synthetic workflows
|-- reports/           Bundled derived HTML reports and figures
|-- references/        Project references and reproducible delay evidence
|-- docker/            Compatibility support for collection tests
|-- .github/workflows/ Offline continuous integration
|-- Dockerfile         Portable runtime and test image
|-- compose.yaml       Report, analysis, and test services
`-- pyproject.toml     Package and dependency configuration
```

Generated outputs belong under the ignored `outputs/` directory. Bundled report
artifacts remain under `reports/`. Raw client gaze files and recordings are not
included in the repository.

## Documentation

- `docs/user_guide.md`: collection, analysis, outputs, and troubleshooting.
- `docs/docker_guide.md`: report hosting, analysis, and tests with Docker.
- `docs/research_collection_protocol.md`: metadata-complete repeated collection.
- `docs/hardware_validation_checklist.md`: laboratory acceptance checks.
- `docs/developer_guide.md`: extension rules and verification expectations.
- `docs/architecture.md`: package boundaries and standard data tables.
- `docs/metrics.md`: quality checks, metrics, units, and interpretation limits.
- `docs/requirements_traceability.md`: project requirements mapped to evidence.
- `docs/technical_report.md`: design decisions, validation, and limitations.

## Install

Python 3.11 is recommended for the full offline and video workflow.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,video]"
.\.venv\Scripts\python.exe -c "import openet2; print('OpenET 2 is ready')"
```

On a laboratory computer used for live acquisition, install the collection
dependencies as well:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,video,collection]"
```

The offline pipeline does not require an eye-tracker SDK. Live Tobii collection
requires the licensed official Tobii Pro SDK and supported hardware.

## Quick start

### Open the bundled reports with Docker

```powershell
docker compose up --build -d report
```

Open <http://localhost:8080/> and stop the service with:

```powershell
docker compose down
```

### Analyse the small example

```powershell
openet2 run `
  --data-root "examples\example_data" `
  --output-root "outputs\example" `
  --expected-marker-events 2
```

### Generate a repeated synthetic workflow

```powershell
openet2 generate-example --output-root "outputs\synthetic_longitudinal_data"
openet2 run `
  --data-root "outputs\synthetic_longitudinal_data" `
  --output-root "outputs\synthetic_longitudinal_report"
```

Synthetic data verifies software behaviour and participant-matched comparison.
It is not evidence of physical eye-tracker performance.

### Analyse an authorised dataset

```powershell
openet2 run `
  --data-root "<path-to-authorised-data>" `
  --output-root "outputs\benchmark" `
  --recover-targets-from-video `
  --client-delay-evidence "references\client_delay_comparison"
```

The input data remains read-only. Video target recovery is accepted only when
the complete protocol passes validation. Delay evidence remains separate from
session metrics and uses explicitly labelled assumed display-field-of-view
scores rather than measured physical visual angles.

### Rehearse collection without hardware

```powershell
openet2 collect `
  --legacy-code-root "docker\legacy_code" `
  --output-root "outputs\collection" `
  --subject-id "DEMO01" `
  --device-id "GP3HD" `
  --test-id "Accuracy" `
  --test-condition "standard" `
  --duration-s 30 `
  --display-width-mm 530 `
  --display-height-mm 300 `
  --viewing-distance-mm 600
```

Collection is a dry run unless `--live` is supplied. Use
`--calibration-confirmed` only after real device calibration has completed.

## Outputs

An analysis run writes standardised tables, quality reports, benchmark metrics,
target-level summaries, repeated-measurement summaries, figures, session reviews,
an HTML report, an input provenance inventory, and a run manifest beneath the
selected output directory.

Important interpretation boundaries:

- Coordinate-unit results must not be described as degrees or pixels.
- Visual-angle metrics require measured display geometry and viewing distance.
- Cross-sectional dates do not establish device drift when participants differ.
- Synthetic outputs demonstrate the pipeline, not hardware performance.
- Application timing does not measure physical pixel-onset latency.

See `docs/metrics.md` and the evidence-status panel in each report before using
results in a study conclusion.

## Verification

Run the offline test suite locally:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider
```

Or run it in the project container:

```powershell
docker compose --profile test run --rm test
```

Live GP3 and Tobii behaviour, SDK compatibility, display selection, achieved
frame rate, and physical timing require laboratory validation with
`docs/hardware_validation_checklist.md`.
