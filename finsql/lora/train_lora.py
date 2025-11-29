"""
TogetherAI LoRA Fine-Tuning Script
Uploads training data and launches fine-tuning jobs for all 4 plugins
"""
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from together import Together
from shared.config import TOGETHER_API_KEY
from finsql.config import (
    LORA_CONFIG,
    TRAINING_CONFIG,
    PLUGIN_CONFIG,
    PLUGIN_REGISTRY_PATH,
    REPO_ROOT
)


class LoRATrainer:
    """Manage TogetherAI LoRA fine-tuning"""

    def __init__(self):
        self.client = Together(api_key=TOGETHER_API_KEY)
        self.training_dir = REPO_ROOT / "data" / "finsql" / "training_data"
        self.base_model = "meta-llama/Meta-Llama-3.1-8B-Instruct-Reference"

        # Training files mapping
        self.training_files = {
            "cot_specialist": self.training_dir / "cot_training.jsonl",
            "robustness_specialist": self.training_dir / "synonym_training.jsonl",
            "structure_specialist": self.training_dir / "skeleton_training.jsonl",
            "hard_cases_specialist": self.training_dir / "hard_training.jsonl"
        }

    # =====================
    # File Upload
    # =====================

    def upload_training_file(self, filepath: Path, purpose: str = "fine-tune") -> str:
        """
        Upload training file to TogetherAI

        Args:
            filepath: Path to JSONL training file
            purpose: File purpose (default: "fine-tune")

        Returns:
            File ID from TogetherAI
        """
        print(f"\n  Uploading {filepath.name}...")

        # TogetherAI expects file path as string, not file object
        response = self.client.files.upload(
            file=str(filepath),
            purpose=purpose
        )

        file_id = response.id
        print(f"  ✓ Uploaded: {file_id}")

        return file_id

    # =====================
    # Fine-Tuning Job
    # =====================

    def create_fine_tune_job(
        self,
        training_file_id: str,
        plugin_name: str,
        model: Optional[str] = None
    ) -> str:
        """
        Create fine-tuning job on TogetherAI

        Args:
            training_file_id: ID of uploaded training file
            plugin_name: Name of the plugin being trained
            model: Base model (default: Meta-Llama-3.1-8B-Instruct-Reference)

        Returns:
            Fine-tune job ID
        """
        if model is None:
            model = self.base_model

        print(f"\n  Creating fine-tune job for {plugin_name}...")

        # Create fine-tuning job
        # TogetherAI expects flat parameters, not nested dicts
        response = self.client.fine_tuning.create(
            training_file=training_file_id,
            model=model,

            # Training hyperparameters (flat, not nested)
            n_epochs=TRAINING_CONFIG["epochs"],
            learning_rate=TRAINING_CONFIG["learning_rate"],
            batch_size=TRAINING_CONFIG["batch_size"],
            warmup_ratio=TRAINING_CONFIG["warmup_steps"] / 100,

            # LoRA parameters (flat)
            lora_r=LORA_CONFIG["rank"],
            lora_alpha=LORA_CONFIG["alpha"],
            lora_dropout=LORA_CONFIG["dropout"],
            lora_trainable_modules=",".join(LORA_CONFIG["target_modules"]),

            # Job metadata
            suffix=plugin_name,
        )

        job_id = response.id
        print(f"  ✓ Job created: {job_id}")

        return job_id

    # =====================
    # Monitor Training
    # =====================

    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check status of fine-tuning job

        Args:
            job_id: Fine-tune job ID

        Returns:
            Job status dict
        """
        response = self.client.fine_tuning.retrieve(job_id)

        return {
            "id": response.id,
            "status": response.status,
            "model": getattr(response, 'fine_tuned_model', None),
            "created_at": response.created_at,
            "finished_at": getattr(response, 'finished_at', None),
            "error": getattr(response, 'error', None)
        }

    def wait_for_completion(
        self,
        job_id: str,
        check_interval: int = 60,
        timeout: int = 7200  # 2 hours
    ) -> Dict[str, Any]:
        """
        Wait for fine-tuning job to complete

        Args:
            job_id: Fine-tune job ID
            check_interval: Seconds between status checks
            timeout: Maximum wait time in seconds

        Returns:
            Final job status
        """
        print(f"\n  Waiting for job {job_id} to complete...")
        print(f"  (Checking every {check_interval}s, timeout: {timeout}s)")

        elapsed = 0
        while elapsed < timeout:
            status = self.check_job_status(job_id)

            if status["status"] == "succeeded":
                print(f"\n  ✓ Training completed!")
                print(f"  Fine-tuned model: {status['model']}")
                return status

            elif status["status"] == "failed":
                print(f"\n  ✗ Training failed!")
                print(f"  Error: {status.get('error', 'Unknown error')}")
                return status

            elif status["status"] in ["pending", "running"]:
                print(f"  Status: {status['status']} (elapsed: {elapsed}s)")
                time.sleep(check_interval)
                elapsed += check_interval

            else:
                print(f"  Unknown status: {status['status']}")
                time.sleep(check_interval)
                elapsed += check_interval

        print(f"\n  ⚠️  Timeout reached ({timeout}s)")
        return self.check_job_status(job_id)

    # =====================
    # Plugin Registry
    # =====================

    def save_plugin_registry(self, registry: Dict[str, str]):
        """
        Save plugin adapter IDs to registry file

        Args:
            registry: Dict mapping plugin names to adapter IDs
        """
        PLUGIN_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(PLUGIN_REGISTRY_PATH, 'w') as f:
            json.dump(registry, f, indent=2)

        print(f"\n✓ Plugin registry saved to: {PLUGIN_REGISTRY_PATH}")

    def load_plugin_registry(self) -> Dict[str, str]:
        """Load plugin registry if exists"""
        if PLUGIN_REGISTRY_PATH.exists():
            with open(PLUGIN_REGISTRY_PATH, 'r') as f:
                return json.load(f)
        return {}

    # =====================
    # Train All Plugins
    # =====================

    def train_all_plugins(
        self,
        wait_for_completion: bool = True,
        auto_save: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Upload data and launch training for all 4 plugins

        Args:
            wait_for_completion: Whether to wait for jobs to finish
            auto_save: Whether to save plugin registry automatically

        Returns:
            Dict mapping plugin names to job info
        """
        print("\n" + "="*80)
        print("FINSQL LORA FINE-TUNING")
        print("="*80)

        print(f"\nBase model: {self.base_model}")
        print(f"LoRA rank: {LORA_CONFIG['rank']}")
        print(f"LoRA alpha: {LORA_CONFIG['alpha']}")
        print(f"Target modules: {LORA_CONFIG['target_modules']}")
        print(f"Epochs: {TRAINING_CONFIG['epochs']}")
        print(f"Learning rate: {TRAINING_CONFIG['learning_rate']}")

        results = {}

        # Step 1: Upload all training files
        print(f"\n{'='*80}")
        print("STEP 1: UPLOADING TRAINING FILES")
        print(f"{'='*80}")

        file_ids = {}
        for plugin_name, filepath in self.training_files.items():
            if not filepath.exists():
                print(f"\n✗ File not found: {filepath}")
                continue

            print(f"\n{plugin_name}:")
            file_id = self.upload_training_file(filepath)
            file_ids[plugin_name] = file_id

        # Step 2: Create fine-tuning jobs
        print(f"\n{'='*80}")
        print("STEP 2: CREATING FINE-TUNING JOBS")
        print(f"{'='*80}")

        job_ids = {}
        for plugin_name, file_id in file_ids.items():
            print(f"\n{plugin_name}:")
            job_id = self.create_fine_tune_job(file_id, plugin_name)
            job_ids[plugin_name] = job_id

            results[plugin_name] = {
                "file_id": file_id,
                "job_id": job_id,
                "status": "pending"
            }

        print(f"\n{'='*80}")
        print(f"✓ {len(job_ids)} FINE-TUNING JOBS LAUNCHED")
        print(f"{'='*80}")

        # Step 3: Wait for completion (optional)
        if wait_for_completion:
            print(f"\n{'='*80}")
            print("STEP 3: WAITING FOR TRAINING TO COMPLETE")
            print(f"{'='*80}")
            print("\n⚠️  This may take 30-60 minutes per job...")
            print("You can safely interrupt and check status later.\n")

            plugin_registry = {}

            for plugin_name, job_id in job_ids.items():
                print(f"\n{'-'*80}")
                print(f"Plugin: {plugin_name}")
                print(f"{'-'*80}")

                final_status = self.wait_for_completion(job_id)
                results[plugin_name].update(final_status)

                # Save adapter ID if succeeded
                if final_status["status"] == "succeeded" and final_status["model"]:
                    plugin_registry[plugin_name] = final_status["model"]

            # Save plugin registry
            if auto_save and plugin_registry:
                self.save_plugin_registry(plugin_registry)

        else:
            print("\n⚠️  Jobs launched but not waiting for completion.")
            print("Check status later with: check_training_status()")

        return results

    # =====================
    # Status Checking
    # =====================

    def check_all_jobs_status(self, job_ids: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Check status of all training jobs

        Args:
            job_ids: Dict mapping plugin names to job IDs

        Returns:
            Dict mapping plugin names to status info
        """
        print("\n" + "="*80)
        print("TRAINING JOBS STATUS")
        print("="*80 + "\n")

        results = {}
        plugin_registry = {}

        for plugin_name, job_id in job_ids.items():
            status = self.check_job_status(job_id)
            results[plugin_name] = status

            print(f"{plugin_name}:")
            print(f"  Job ID: {job_id}")
            print(f"  Status: {status['status']}")
            if status.get('model'):
                print(f"  Model: {status['model']}")
                plugin_registry[plugin_name] = status['model']
            if status.get('error'):
                print(f"  Error: {status['error']}")
            print()

        # Save registry if all jobs completed
        all_succeeded = all(s['status'] == 'succeeded' for s in results.values())
        if all_succeeded and plugin_registry:
            print("✓ All jobs completed successfully!")
            self.save_plugin_registry(plugin_registry)

        return results


# =====================
# Main Script
# =====================

def main():
    """Main training script"""
    import argparse

    parser = argparse.ArgumentParser(description="Fine-tune FinSQL LoRA plugins")
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Launch jobs but don't wait for completion"
    )
    parser.add_argument(
        "--check-status",
        nargs='+',
        help="Check status of existing jobs (provide job IDs)"
    )

    args = parser.parse_args()

    trainer = LoRATrainer()

    if args.check_status:
        # Check status of specific jobs
        job_ids = {f"job_{i}": job_id for i, job_id in enumerate(args.check_status)}
        trainer.check_all_jobs_status(job_ids)
    else:
        # Launch new training
        results = trainer.train_all_plugins(
            wait_for_completion=not args.no_wait,
            auto_save=True
        )

        print("\n" + "="*80)
        print("TRAINING SUMMARY")
        print("="*80 + "\n")

        for plugin_name, info in results.items():
            print(f"{plugin_name}:")
            print(f"  File ID: {info.get('file_id', 'N/A')}")
            print(f"  Job ID: {info.get('job_id', 'N/A')}")
            print(f"  Status: {info.get('status', 'unknown')}")
            if info.get('model'):
                print(f"  Model: {info['model']}")
            print()


if __name__ == "__main__":
    main()
