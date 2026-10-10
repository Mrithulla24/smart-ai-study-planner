from ai_model import predict_priority

def generate_recommendations(performance_data):
    recommendations=[]
    for item in performance_data:
        score=float(item['score']); attendance=float(item['attendance']); study_hours=float(item['study_hours']); previous=float(item['previous_score'])
        priority=predict_priority(score,attendance,study_hours,previous)
        change=score-previous; reasons=[]
        if score<50: reasons.append('Very low score')
        elif score<70: reasons.append('Average score')
        if attendance<75: reasons.append('Low attendance')
        if study_hours<2: reasons.append('Increase study hours')
        if change<0: reasons.append('Performance has decreased')
        elif change>0: reasons.append('Performance has improved')
        text=', '.join(reasons) if reasons else 'Performance is satisfactory'
        hours=4.0 if priority=='HIGH' else 2.5 if priority=='MEDIUM' else 1.5
        recommendations.append({'subject_id':item['subject_id'],'subject_name':item['subject_name'],'topic':item.get('topic',''),'score':score,'attendance':attendance,'study_hours':study_hours,'previous_score':previous,'score_change':change,'priority':priority,'recommended_hours':hours,'recommendation':text})
    return recommendations

def generate_study_plan(recommendations):
    return [{'subject_id':x['subject_id'],'subject_name':x['subject_name'],'topic':x.get('topic',''),'recommended_hours':x['recommended_hours'],'priority':x['priority'],'recommendation':x['recommendation'],'status':'PENDING'} for x in recommendations]
