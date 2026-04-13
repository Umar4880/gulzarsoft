def add_summary(existing_summaries: dict, new_summaries):
    merged = existing_summaries.copy()
    
    for url, summary in new_summaries.items():
        merged[url] = summary

    return merged

