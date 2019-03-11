#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define SIZE 10000

int main(void) {
	char file_name[100];
	char new_file_name[100];
	char buffer[SIZE];
	int cur = 0;
	int search_size;
	int length;
	
	printf("Input the file name: ");
	scanf("%s", file_name);
	printf("Input the new name: ");
	scanf("%s", new_file_name);
	
	//Read & Write file 
	FILE *fptr_r;
	FILE *fptr_w;
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
	
	fptr_w = fopen("log.txt", "a");
	fseek(fptr_w, 0L, SEEK_END);
	if( ftell(fptr_w) !=0 ) {
		fputc('\n', fptr_w);
	}
	
	fprintf(fptr_w, "file copy is done");
	
	fclose(fptr_w);
	
	return 0;
}
			

