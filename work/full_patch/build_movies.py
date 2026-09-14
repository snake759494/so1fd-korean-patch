from pathlib import Path
import sys
P=Path(__file__).parent
sys.path.insert(0,str(P.parent/'story_patch'))
import movie_build as mb
from movie_cues import CUES
mb.OUT=P/'movies';mb.OUT.mkdir(exist_ok=True);mb.CUES=CUES
SOURCES={'13_ronikis_ilia_c':'04_ronikis_ilia','14_timegate_c':'05_timegate','15_feather_girl_c':'06_feather_girl','16_neorevorse_c':'07_neorevorse','17_good_by_c':'08_good_by'}
if __name__=='__main__':
 for name in sys.argv[1:] or CUES:mb.build(name,SOURCES[name])
