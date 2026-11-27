"""Focused routing regressions: do not rewrite a different named recipe."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from chef.recipe_followups_v1 import RecipeFollowupsGraph
class Inner:
 def invoke(self,state):return {'question_seen':state['question']}
graph=RecipeFollowupsGraph(Inner(),None)
def check(q,expected,focus='Menemen'):
 got=graph.invoke({'question':q,'recipe_focus':focus,'history':[]})['question_seen']
 assert got==expected,(q,got,expected)
check('what is the recipe?','give me the recipe for Menemen')
check('what is the recipe for Gazpacho?','what is the recipe for Gazpacho?')
check('what is the recipe?','what is the recipe?',None)
check('give me another recipe','give me another recipe')
print('4 follow-up routing checks passed')
