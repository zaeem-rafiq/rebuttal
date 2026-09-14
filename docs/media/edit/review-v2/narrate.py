import asyncio, json
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parent
async def main():
    scenes=json.loads((ROOT/'scenes.json').read_text())
    for i,scene in enumerate(scenes):
        path=ROOT/f'voice-{i}.mp3'
        if path.exists() and path.stat().st_size: continue
        communicate=edge_tts.Communicate(scene['speech'],'en-US-AndrewMultilingualNeural',rate='-4%',boundary='WordBoundary')
        metadata=[]
        with path.open('wb') as f:
            async for chunk in communicate.stream():
                if chunk['type']=='audio': f.write(chunk['data'])
                elif chunk['type']=='WordBoundary': metadata.append(chunk)
        (ROOT/f'voice-{i}.json').write_text(json.dumps(metadata,indent=2))
        print(f'Generated voice {i}',flush=True)
asyncio.run(main())
