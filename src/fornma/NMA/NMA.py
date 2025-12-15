#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 10 09:11:32 2022

@author: luiza
"""

import argparse
def main(argv=None):

    # Create the parser
    parser = argparse.ArgumentParser(description='Plots NMA Graph for every condition and time specified')

    # Add the arguments
    parser.add_argument('-fc',
                        action='append',
                        dest='collectionc',
                        default=[],
                        required= True,
                        help='Path to result files for every control gorup.',
                        )


    parser.add_argument('-ft',
                        action='append',
                        dest='collectiont',
                        default=[],
                        help='Path to result files for every treated gorup.',
                        )


    parser.add_argument('-s','--save',
                        type = str,
                        help='Path to save results',
                        )


    parser.add_argument('-sd',
                        nargs='?',
                        type=float,
                        default = 2.0,
                        help='Number of standard deviations from mean to use for NMA threshold. This can be adjusted later')


    parser.add_argument('-g', '--graph_type',
                        nargs='?',
                        type= str,
                        default = 'heatmap',
                        help='Type of graph to be plotted. Choose between: heatmap, dot, sample')




    # Execute the parse_args() method
    args = parser.parse_args()



    controls = args.collectionc
    treatments = args.collectiont
    save = args.save
    sd = args.sd
    graph = args.graph_type

    print(controls, treatments, save, sd, graph)



    #pego tudo isso, organizo, crio a classe do NMA, mostro os graficos pra pessoa ajustar
    # mando mensagens na tela que ta plotando e salvando tudo
    # preparo função de chamar se for overtime plota em cada tempo cada condição
    # se não for overtime só separa as condições
    #salva tudo e as porcentagens tbm


if __name__ == "__main__":
    main()


