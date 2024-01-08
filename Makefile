EXEC = trade
SRC = main.py

all:
	@cp $(SRC) $(EXEC)
	@chmod +x $(EXEC)
clean:
	@find . -type f -name '*~' -delete
fclean:	clean
	@$(RM) -f $(EXEC)
re: fclean all
.PHONY:	all clean fclean re