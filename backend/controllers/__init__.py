"""
控制器模块初始化
"""
from .patient_controller import PatientController, default_patient_controller, create_patient_blueprint

__all__ = ['PatientController', 'default_patient_controller', 'create_patient_blueprint']