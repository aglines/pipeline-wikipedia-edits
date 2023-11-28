# Analysis and SQL statements
- Here are some questions I'm curious about, and the SQL I wrote to find out some answers.
- Data consisted of ca. 100000 rows, ingested over about 2 hours (admittedly, a small sample)

## Interesting features and questions about data validity 
- ```pipeline.py``` shows all the columns ingested, but I was most interested in these: 
- The column ```bot``` tells us if the editor of the article was a bot or a human
- Wikipedia notes the new and old lengths of the article. The pipeline calculates that difference, ```edit_length```. 
- The column ```is_minor``` means that the editor thought that the current change was small
    What does "small" mean, exactly? The rule is a bit vague. Wikipedia doesn't require editors to mark this, and there seems to be no check if this data is accurate
- The column ```is_patrolled``` means that the article being edited is currently being watched more closely
    Maybe the article is being vandalized, or it's a contentious subject, or it's about a current event

_________

### 1. Bot editors vs human editors
- How many edits total were made by bots vs human editors?
``` sql
SELECT bot, COUNT(*) AS edit_count, 
ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM `pipeline-wikipedia-edits.dataset01.table01`)), 2) AS percentage_of_total
FROM `pipeline-wikipedia-edits.dataset01.table01`
GROUP BY edited_by_bot
```
- Results: 
```
bot	    edit_count      percentage_of_total
false	61760	        61.45
true	38751	        38.55
```
- Overall there were more human editors in this sample than bot editors, but not really a huge disparity between these editor types 

_________


### 2. Mean edit length, for various categories
- What's the mean edit length, for each of several different categories? 
``` sql
SELECT bot, is_patrolled, is_minor_change, ROUND(AVG(edit_length)) AS mean_edit_length
FROM `pipeline-wikipedia-edits.dataset01.table01`
GROUP BY bot, is_patrolled, is_minor_change
ORDER BY bot, is_patrolled, is_minor_change
```
- Results:
```
bot     is_patrolled	is_minor_change	    mean_edit_length
false	false	        false	            315.0
false	false	        true	            -605.0
false	true	        false	            161.0
false	true	        true	            12.0
true	false	        false	            70.0
true	false	        true	            34.0
true	true	        false	            929.0
true	true	        true	            -3.0
```

_________

### Further questions
- Mean edit lengths for articles marked ```is_minor_change``` are small, except for human editors of non-patrolled articles. This is a remarkably large negative value, -605. 
- Lots of questions stem from outliers like these.  Given time, I would go down logical paths like these: 
    - Did editors remove a large amount somewhere? How "much" of an article is that -605, exactly?
    - ```edit_length``` is in bytes, not characters. Bytes per character depends on the language of the edit, so further analysis would be needed to weight these appropriately
- And, of course: isn't the sample size too small to really make a judgment?

