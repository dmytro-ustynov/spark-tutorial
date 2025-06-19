# Student Work Directory

This directory is mounted into the Spark container for your analytics work.

## Getting Started

1. Start the Spark container:
   ```bash
   ./lab-control.sh spark-shell
   ```

2. Or use Jupyter Lab:
   ```bash
   ./lab-control.sh jupyter
   ```

3. Create your analytics files here and they'll be saved on your host machine.

## Example Files

You can copy templates from the examples directory:
```bash
cp examples/security_analytics_template.py student-work/my_analytics.py
```

Your work will persist even when containers are restarted!
