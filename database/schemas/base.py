"""
This holds the expected formats of the database models in use
"""
from collections import defaultdict


User = defaultdict(lambda: '', {  # string

    "first_name": '',  # string
    "last_name": '',  # string
    "password": '',  # string
    "email": '',  # string
    "date_created": "datetime",  # as ing  # string
})

Teams = defaultdict(lambda: '', {  # string

    "description": "",  # string
    "role": '',  # string
    "name": '',  # string
    "created_at": "datetime",
})

TeamMember = defaultdict(lambda: '', {  # string

    "joined": True or False,
    "user_id": '',  # users id (string)
    "team_id": '',  # teams id (string)
    "role": '',  # string
})

Invites = defaultdict(lambda: '', {  # string

    "is_closed": True or False,
    "invitee": '',  # string
    "role": '',  # string
    "status": '',  # string
    
    "date_created": "datetime",  # as ing  # string

    "sender_id": '',  # senders id (string)
    "team_id": '',  # teams id (string)
})

Environments = defaultdict(lambda: '', {
    "password": "",  # string
    "hostname": "",  # ip address
    "username": "",
    "name": "",
    "use_pkey": True or False,
    "cores": "",
    "processor": "",
    "ram_gb": 0.0,
    "ram_gb": 0.0, 
    "is_provisioned": True or False,  # if in use for inference
    "last_used": "datetime",
    "status": "",

    "user_id": '',  # users id (string)
})

Projects = defaultdict(lambda: '', {  # string

    "description": "",  # string
    "model_id": 0,
    "dataset": '',  # string
    "results": '',  # string
    "created_by": 0,
    "model_source": '',  # string
    "name": '',  # string
    "team_id": 0,

    "batch_size1": 0,
    "batch_size2": 0,
    "batch_size3": 0,

    "created_on": "datetime",
    "created_at": "datetime",

    "user_id": '',  # users id (string)
    "environment_id": '',  # environments id (string)
})

UploadedModels = defaultdict(lambda: '', {  # string

    "user_id": '',  # users id (string)
    "name": '',  # string
    "size": '',  # string
    "framework": '',  # pytorch, tensorflow, and onnx  # string
    "category": '',  # object-detection, image-classification, image-segmentation, etc.
    "created_on": "datetime",
    
    "files": {
        
            "xml": "xml_model_url",
            "bin": "bin_model_url",
            "model": "model_file_url",
            "model_class": "model_class_url",  # for pytorch
        }
    },
})

BenchmarkExperiments = defaultdict(lambda: '', {  # string
    "name": '',  # string
    "status": '',  # string
    "dataset": '',  # string
    "batchsize": 2,

    "created_on": "datetime",

    "user_id": '',  # users id (string)
    "model_id": '',  # modellibrarys id (string)
    "project_id": '',  # projects id (string)
    "environment_id": '',  # environments id (string)
})

FineTuneExperiments = defaultdict(lambda: '', {  # string
    "name": '', 
    
    "created_on": "datetime",

    "user_id": '',  # users id (string)
    "model_id": '',  # modellibrarys id (string)
    "project_id": '',  # projects id (string)
    "environment_id": '',  # environments id (string)
})

Experiments = defaultdict(lambda: '', {  # string  # previously runs
    "type": "",  # experiment type
    
    # TODO: update this
    "accuracy": 0.0,
    "latency": 0.0,
    "cpu_usage": 0.0,
    "throughput": 0.0,
    "batch_latency": 0.0,
    "memory_footprint": 0.0,
    "batch_throughput": 0.0,

    "user_id": '',  # users id (string)
    "experiment_id": '',  # experiments id (string)
})