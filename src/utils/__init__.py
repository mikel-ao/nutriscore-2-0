#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo utils - Food Safety Analysis Pipeline

Contiene:
- pipeline_maestro: Orquestación completa del pipeline
- ssi_pipeline: Funciones para análisis SSI
- food_classification_pipeline: Funciones de clustering
- data_loader: Carga de datos
- logger: Logger centralizado
"""

from .pipeline_maestro import Config, Logger, main

__all__ = ['Config', 'Logger', 'main']
__version__ = '4.0'
