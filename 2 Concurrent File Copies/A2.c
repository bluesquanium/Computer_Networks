#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <process.h>
#include <time.h>

#define SIZE 10000

char input[100];
char output[100];
clock_t start_t, end_t;

unsigned _stdcall Thread_Copier(void *arg) {
	char file_name[100];
	char new_file_name[100];
	strcpy(file_name, input); // copy the file_name
	strcpy(new_file_name, output);// copy the new_file_name
	
	char buffer[SIZE];
	int cur = 0;
	int search_size;
	int length;
	
	FILE *fptr_r;
	FILE *fptr_w;
	
	//Record start log
	end_t = clock();
	fptr_w = fopen("log.txt", "a");
	fseek(fptr_w, 0L, SEEK_END);
	fprintf(fptr_w, "%.2f\tStart copying %s to %s\n",(float)(end_t-start_t)/CLOCKS_PER_SEC, file_name, new_file_name);
	fclose(fptr_w);
	
	//Read & Write file 
	fptr_r = fopen(file_name, "rb");
	fptr_w = fopen(new_file_name, "wb");
	
	if(fptr_r==NULL) {
		printf("File Error\n");
		exit(1);
	}

	cur = ftell(fptr_r);
	fseek(fptr_r, 0L, SEEK_END);
	search_size = ftell(fptr_r) - cur;
	if( search_size >= SIZE ) {
		search_size = SIZE;
	}
	fseek(fptr_r, cur, SEEK_SET);
	
	while( (fread(buffer, 1, search_size, fptr_r))!=0 ) {
		fwrite(buffer, 1, search_size, fptr_w);
		cur = ftell(fptr_r);
		fseek(fptr_r, 0L, SEEK_END);
		search_size = ftell(fptr_r) - cur;
		
		if( search_size >= SIZE ) {
			search_size = SIZE;
		}
		
		fseek(fptr_r, cur, SEEK_SET);
	}
	
	fclose(fptr_r);
	fclose(fptr_w);
	
	end_t = clock();
	fptr_w = fopen("log.txt", "a");
	fseek(fptr_w, 0L, SEEK_END);
	fprintf(fptr_w, "%.2f\t%s is copied completely\n",(float)(end_t-start_t)/CLOCKS_PER_SEC, new_file_name);
	fclose(fptr_w);
	
	_endthread();
}

int main(void) {
	start_t = clock();
	
	while(1) {
		printf("Input the file name: ");
		scanf("%s", input);
		printf("Input the new name: ");
		scanf("%s", output);
		putchar('\n');
		
		_beginthreadex(NULL, 0, Thread_Copier, 0, 0, NULL);
	}
	
	return 0;
}
			

