import pickle
import pandas as pd
from matplotlib import *
from matplotlib import pyplot as plt
import numpy as np
import mlflow

def loadDictionaryFromPickleFile(dictionaryPath):
    ''' Load the pickle file as a dictionary
    Args:
        dictionaryPath: path to the pickle file
    Return: dictionary from the pickle file
    '''
    with open(dictionaryPath, 'rb') as filePointer:
        dictionary = pickle.load(filePointer)
    return dictionary

def saveDictionaryAsPickleFile(dictionary, dictionaryPath):
    ''' Save dictionary as a pickle file
    Args:
        dictionary to be saved
        dictionaryPath: filepath to which the dictionary will be saved
    '''
    with open(dictionaryPath, 'wb') as filePointer:
        pickle.dump(dictionary, filePointer, protocol=pickle.HIGHEST_PROTOCOL)

def calcMetrics(max_k, k_range, resultFile, gtPath=None, resPath=None, record=True, verbose=False):
    '''Calculate and log the performance metrics, both system-wide and per-query.
    
    Args:
        max_k: maximum K value (10 for SANTOS, 60 for TUS)
        k_range: step size for K values
        resultFile: dictionary containing search results
        gtPath: path to groundtruth pickle file
        resPath: (deprecated) path to results file
        record: whether to log to MLFlow
        verbose: whether to print intermediate results
        
    Returns:
        Dictionary containing both system-wide metrics and per-query metrics.
    '''
    groundtruth = loadDictionaryFromPickleFile(gtPath)
    
    # Initialize system-wide metrics arrays
    system_precision = np.zeros(max_k)
    system_recall = np.zeros(max_k)
    system_map = np.zeros(max_k)
    system_f1 = np.zeros(max_k)
    
    # Initialize per-query results
    per_query_metrics = {}
    
    # Process each query
    for query_id, results in resultFile.items():
        if query_id not in groundtruth:
            continue
            
        query_metrics = {
            'candidates': results,              # Retrieved results
            'ground_truth': groundtruth[query_id],  # Ground truth for the query
            'precision': [],
            'recall': [],
            'ap': []  # Average precision at each k
        }
        
        gt_set = set(groundtruth[query_id])
        total_relevant = len(gt_set)
        
        # Calculate metrics at each k for this query
        for k in range(1, max_k + 1):
            current_results = results[:k]
            result_set = set(current_results)
            intersect = result_set.intersection(gt_set)
            
            # Calculate precision and recall for current k
            precision = len(intersect) / k if k > 0 else 0
            recall = len(intersect) / total_relevant if total_relevant > 0 else 0
            
            query_metrics['precision'].append(precision)
            query_metrics['recall'].append(recall)
            
            # Add to system-wide metrics
            system_precision[k-1] += precision
            system_recall[k-1] += recall
            
            # Correct AP@k calculation:
            # Sum precision at ranks where the retrieved item is relevant.
            ap_k = 0.0
            num_relevant_found = 0
            for i in range(1, k+1):
                if current_results[i-1] in gt_set:
                    num_relevant_found += 1
                    precision_at_i = num_relevant_found / i
                    ap_k += precision_at_i
            # Normalize by min(k, total_relevant) if there are any relevant items
            norm = min(k, total_relevant) if total_relevant > 0 else 1
            ap_k = ap_k / norm
            query_metrics['ap'].append(ap_k)
        
        per_query_metrics[query_id] = query_metrics
    
    # Compute system-wide averages
    num_queries = len(per_query_metrics)
    if num_queries > 0:
        system_precision /= num_queries
        system_recall /= num_queries
        system_map = np.mean([metrics['ap'] for metrics in per_query_metrics.values()], axis=0)
        
        # Calculate F1 scores for each k
        system_f1 = 2 * (system_precision * system_recall) / (system_precision + system_recall)
        system_f1 = np.nan_to_num(system_f1)  # Replace NaN (from division by zero) with 0
    
    # Determine k values used for evaluation based on k_range
    used_k = [k_range]
    if max_k > k_range:
        for i in range(k_range * 2, max_k+1, k_range):
            used_k.append(i)
    
    # Store system-wide metrics at the specified k points
    metrics_at_k = {}
    for k in used_k:
        metrics_at_k[k] = {
            'precision': float(system_precision[k-1]),
            'recall': float(system_recall[k-1]),
            'map': float(system_map[k-1]),
            'f1': float(system_f1[k-1])
        }
    
    if record:
        mlflow.log_metric("mean_avg_precision", system_map[-1])
        mlflow.log_metric("prec_k", system_precision[-1])
        mlflow.log_metric("recall_k", system_recall[-1])
        mlflow.log_metric("f1_k", system_f1[-1])
    
    return {
        'system_metrics': {
            'precision': system_precision.tolist(),
            'recall': system_recall.tolist(),
            'map': system_map.tolist(),
            'f1': system_f1.tolist(),
            'used_k': used_k,
            'metrics_at_k': metrics_at_k
        },
        'per_query_metrics': per_query_metrics
    }