''' transfer the text-only dataset into text token ID
'''
import json
import os
import sys
import torch
import torch.nn.functional as F
import argparse
import logging
from collections import defaultdict
import torchaudio
#from tools.tokenizer.MimiCodec.mimi_tokenizer import MimiTokenizer
from tools.tokenizer.Text2ID.text_tokenizer import TextTokenizer


def get_parser():
    parser = argparse.ArgumentParser(
        description="convert a data list, do tokenization and save as a torch .pt file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-file", type=str, default=None, help="utt2json in the format <exampe_id> <json_path>")
    parser.add_argument("--output-file", type=str, help="the output .pt file")
    parser.add_argument("--checkpoint_dir", type=str, help='the path of')
    parser.add_argument("--rank", type=int, help="local GPU rank, if applicable")
    return parser

def main(args):
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format=f"%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
    )
    args = get_parser().parse_args(args)
    args.rank -= 1 # run.pl starts from 1 but the exact jobid / gpuid starts from 0   
    max_gpu = torch.cuda.device_count()
    args.rank = (args.rank % max_gpu)
    data_dict = {}
    text_tokenizer = TextTokenizer(checkpoint_dir=args.checkpoint_dir)
    logging.info('Text tokenizer built')
    import time
    st_time = time.time()
    with open(args.input_file, "r") as utt2json:
        for line in utt2json:
            name, json_path = line.strip().split(' ')

            text = ""
            with open(json_path, "r") as f:
                session = json.load(f)
                for itm in session["segments"]:
                    speaker_id = int(itm["speaker"].split("_")[-1])
                    text += f" [{speaker_id}]{itm['text']}"
            
            text = text.strip()
            ids = text_tokenizer.tokenize_text(text)
            ids = torch.Tensor(ids).to(torch.int32)
            data_dict[name] = ids
    torch.save(data_dict, args.output_file)
    ed_time = time.time()
    logging.info(f"processed {ed_time-st_time} seconds")


if __name__ == "__main__":
    main(sys.argv[1:])
    