# AIIIR
A hardware system and software suite for comprehensive air quality monitoring

## Repo Structure
- `src/` : Python code for Detective (analytics system) and Sentry (alerts system).
- `/plots` : Graph visualizations for forecasting, frequency analysis and outlier detection.
- `/ESW_Proj.ino` : Arduino code.
- `/alert_config.json` : Config file to set bounds for the different parameters; Sentry sends alerts only if these are exceeded.
- `/final_grafanaconfig.json` : Final Grafana dashboard config file.
- `/team5-esw-proj-report.pdf` : Comprehensive report that dives into the overall implementation in great detail. Section Five contains instructions to build the dashboard on Grafana Cloud using the config file.
